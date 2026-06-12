import { IncomingMessage, ServerResponse } from "http";
import { Plugin } from "vite";
import * as http from "http";

const A2UI_MIME_TYPE = "application/json+a2ui";

export function a2aMiddleware(): Plugin {
  return {
    name: "a2a-middleware",
    configureServer(server) {
      server.middlewares.use("/a2a", async (req: IncomingMessage, res: ServerResponse, next: any) => {
        console.log(`[PROXY] Incoming request: ${req.method} ${req.url}`);
        if (req.method !== "POST") return next();

        let body = "";
        req.on("data", (chunk) => body += chunk);
        req.on("end", async () => {

          let parsedBody;
          try {
            parsedBody = JSON.parse(body);
          } catch (e) {
            res.statusCode = 400;
            return res.end(JSON.stringify({ error: "Invalid JSON" }));
          }

          // 1. Create Session (or Reuse)
          console.log("[PROXY] Setting up ADK User Session...");
          const appName = "route_planner_agent_a2ui";
          const userId = "test-user";

          // Simple in-memory cache for the proxy lifetime
          // @ts-ignore
          if (!global.proxySessionId) {
            console.log("[PROXY] No active session found. Creating new one...");
            const sessionReqOpts = {
              hostname: '127.0.0.1',
              port: 8000,
              path: `/apps/${appName}/users/${userId}/sessions`,
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              }
            };

            const sessionId = await new Promise<string>((resolve, reject) => {
              const creq = http.request(sessionReqOpts, (cres) => {
                let cdata = '';
                cres.on('data', chunk => cdata += chunk);
                cres.on('end', () => {
                  console.log("[PROXY] Session Endpoint Response:", cdata);
                  try {
                    const js = JSON.parse(cdata);
                    resolve(js.id || js.sessionId);
                  } catch (e) { reject(e); }
                });
              });
              creq.on('error', reject);
              creq.write(JSON.stringify({ appName, userId }));
              creq.end();
            });
            // @ts-ignore
            global.proxySessionId = sessionId;
          } else {
            console.log("[PROXY] Reusing existing session:", global.proxySessionId);
          }

          // @ts-ignore
          const sessionId = global.proxySessionId;

          // 2. Format RunSseRequest according to Content-Input scheme
          const txt = parsedBody.params?.message?.parts?.[0]?.text || "Hello";
          console.log("[PROXY] Session created:", sessionId, "Formatting SSE for text:", txt);
          const runBody = JSON.stringify({
            appName,
            userId,
            sessionId: sessionId,
            newMessage: { parts: [{ text: txt }] }
          });

          const runReqOpts = {
            hostname: '127.0.0.1',
            port: 8000,
            path: '/run_sse',
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Content-Length': Buffer.byteLength(runBody)
            }
          };

          const runReq = http.request(runReqOpts, (runRes) => {
            // We want to pass the SSE stream or data back to the client cleanly
            let allData = '';
            runRes.on('data', chunk => allData += chunk);
            runRes.on('end', () => {
              // For the proxy, we parse the SSE and return the A2UI json.
              let accumulatedText = "";
              const parts: any[] = [];
              const lines = allData.split('\n');
              for (let line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    let lineData = line.substring(6).trim();
                    if (lineData === '[DONE]') continue;
                    const js = JSON.parse(lineData);

                    if (js.content && Array.isArray(js.content.parts)) {
                      for (const part of js.content.parts) {
                        if (part.text) {
                          accumulatedText += part.text;
                        }
                      }
                    }
                  } catch (e) {
                    // Log the first 50 chars of the failed line to debug without overflowing terminal
                    console.error(`[PROXY] parse fail on line (len ${line.length}): ${line.substring(0, 50)}...`, e.message);
                  }
                }
              }

              // Post-process the accumulated text to find the A2UI JSON payload
              console.log("[PROXY] Accumulated text length:", accumulatedText.length, "Includes marker:", accumulatedText.includes('---a2ui_JSON---'));
              let a2uiPayload = null;
              if (accumulatedText.includes('---a2ui_JSON---')) {
                const partsStr = accumulatedText.split('---a2ui_JSON---');
                const conversationText = partsStr[0].trim();

                // Add conversational intro text
                if (conversationText) {
                  parts.push({ kind: "text", text: conversationText });
                }

                // Parse A2UI json
                try {
                  let jsonStr = partsStr[1].trim();
                  if (jsonStr.startsWith('```json')) jsonStr = jsonStr.substring(7);
                  if (jsonStr.endsWith('```')) jsonStr = jsonStr.substring(0, jsonStr.length - 3);

                  const parsedComponents = JSON.parse(jsonStr);
                  // Agent outputs an array of components or a single wrapper
                  if (Array.isArray(parsedComponents)) {
                    parsedComponents.forEach(cmp => {
                      parts.push({ kind: "data", data: cmp, metadata: { mimeType: A2UI_MIME_TYPE } });
                    });
                  } else {
                    parts.push({ kind: "data", data: parsedComponents, metadata: { mimeType: A2UI_MIME_TYPE } });
                  }
                  console.log("[PROXY] Successfully parsed A2UI payload components:", parts.length);
                } catch (e) {
                  console.error("[PROXY] Failed to parse A2UI JSON payload", e);
                }
              } else {
                // Fallback: If no A2UI json is detected, just return the raw text
                parts.push({ kind: "text", text: accumulatedText });
              }

              res.statusCode = 200;
              res.setHeader("Content-Type", "application/json");

              // Wrap the response in the JSON-RPC format expected by A2AClient
              const rpcResponse = {
                jsonrpc: "2.0",
                id: parsedBody.id,
                result: {
                  kind: "task",
                  status: {
                    state: "finished",
                    message: { parts }
                  }
                }
              };
              res.end(JSON.stringify(rpcResponse));
            });
          });

          runReq.on('error', (e) => {
            console.error("[PROXY] Error on /run_sse request:", e.message);
            res.statusCode = 500;
            res.end(JSON.stringify({ error: e.message }));
          });
          runReq.write(runBody);
          runReq.end();

        });
      });
    },
  };
}
