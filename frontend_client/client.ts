/*
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */

import { Part, SendMessageSuccessResponse, Task } from "@a2a-js/sdk";
import { A2AClient } from "@a2a-js/sdk/client";
import { v0_8 } from "@a2ui/lit";

const A2UI_MIME_TYPE = "application/json+a2ui";

export class A2UIClient {
  #serverUrl: string;
  #client: A2AClient | null = null;

  constructor(serverUrl: string = "") {
    this.#serverUrl = serverUrl;
  }

  #ready: Promise<void> = Promise.resolve();
  get ready() {
    return this.#ready;
  }

  async #getClient() {
    if (!this.#client) {
      // Default to window.location.origin if no URL provided (fallback for proxy mode)
      const baseUrl = this.#serverUrl || window.location.origin;

      console.log("[A2UI] Initializing A2AClient with baseUrl:", baseUrl);
      this.#client = await A2AClient.fromCardUrl(
        `${baseUrl}/.well-known/agent-card.json?t=${Date.now()}`,
        {
          fetchImpl: async (url, init) => {
            console.log(`[A2UI] Fetching: ${url}`, init);
            const headers = new Headers(init?.headers);
            headers.set("X-A2A-Extensions", "https://a2ui.org/a2a-extension/a2ui/v0.8");
            try {
              const res = await fetch(url, { ...init, headers });
              console.log(`[A2UI] Fetch success: ${url} -> ${res.status}`);
              return res;
            } catch (e) {
              console.error(`[A2UI] Fetch failed: ${url}`, e);
              throw e;
            }
          }
        }
      );
    }
    return this.#client;
  }

  async send(
    message: v0_8.Types.A2UIClientEventMessage | string
  ): Promise<v0_8.Types.ServerToClientMessage[]> {
    const client = await this.#getClient();

    console.log("[A2UI] Preparing to send message content:", message);
    let parts: Part[] = [];

    if (typeof message === 'string') {
      // Try to parse as JSON first, just in case
      try {
        const parsed = JSON.parse(message);
        if (typeof parsed === 'object' && parsed !== null) {
          parts = [{
            kind: "data",
            data: parsed as unknown as Record<string, unknown>,
            mimeType: A2UI_MIME_TYPE,
          } as Part];
        } else {
          parts = [{ kind: "text", text: message }];
        }
      } catch {
        // Check for A2UI delimiter
        const delimiter = "---a2ui_JSON---";
        if (message.includes(delimiter)) {
          const [textPart, jsonPart] = message.split(delimiter);

          if (textPart.trim()) {
            parts.push({ kind: "text", text: textPart.trim() });
          }

          if (jsonPart.trim()) {
            try {
              const parsed = JSON.parse(jsonPart.trim());
              parts.push({
                kind: "data",
                data: parsed as unknown as Record<string, unknown>,
                // mimeType is not in DataPart type? Check SDK, but remove if erroring.
                // data: parsed as ..., mimeType: ...
              } as Part);
            } catch (e) {
              console.error("[A2UI] Failed to parse A2UI JSON part:", e);
              // Fallback: treat JSON part as text if parsing fails, or just ignore?
              // Let's treat as text to be safe/visible
              parts.push({ kind: "text", text: `[A2UI Parse Error] ${jsonPart.trim()}` });
            }
          }
        } else {
          parts = [{ kind: "text", text: message }];
        }
      }
    } else {
      parts = [{
        kind: "data",
        data: message as unknown as Record<string, unknown>,
        mimeType: A2UI_MIME_TYPE,
      } as Part];
    }

    const response = await client.sendMessage({
      message: {
        messageId: crypto.randomUUID(),
        role: "user",
        parts: parts,
        kind: "message",
      },
    });

    if ("error" in response) {
      console.error("[A2UI] Response error:", response.error);
      throw new Error(response.error.message);
    }
    console.log("[A2UI] Start processing result:", response);

    const result = (response as SendMessageSuccessResponse).result as Task;
    if (result.kind === "task" && result.status.message?.parts) {
      const messages: v0_8.Types.ServerToClientMessage[] = [];
      for (const part of result.status.message.parts) {
        if (part.kind === 'data') {
          messages.push(part.data as v0_8.Types.ServerToClientMessage);
        } else if (part.kind === 'text') {
          const delimiter = "---a2ui_JSON---";
          if (part.text.includes(delimiter)) {
            const [textPart, jsonPart] = part.text.split(delimiter);

            // 1. Handle the text part (if any)
            if (textPart.trim()) {
              const textId = `text-${crypto.randomUUID()}`;
              const surfaceId = `surface-${crypto.randomUUID()}`;
              messages.push({
                beginRendering: { surfaceId, root: textId }
              });
              messages.push({
                surfaceUpdate: {
                  surfaceId,
                  components: [{
                    id: textId,
                    component: { Text: { text: { literalString: textPart.trim() } } }
                  }]
                }
              });
            }

            // 2. Handle the JSON part
            if (jsonPart.trim()) {
              try {
                const parsed = JSON.parse(jsonPart.trim());
                if (Array.isArray(parsed)) {
                  messages.push(...parsed as v0_8.Types.ServerToClientMessage[]);
                } else {
                  console.warn("[A2UI] Parsed JSON is not an array, treating as single message:", parsed);
                  messages.push(parsed as v0_8.Types.ServerToClientMessage);
                }
              } catch (e) {
                console.error("[A2UI] Failed to parse A2UI JSON from agent response:", e);
              }
            }
          } else {
            // Standard Text Handling
            const textId = `text-${crypto.randomUUID()}`;
            const surfaceId = `surface-${crypto.randomUUID()}`;
            messages.push({
              beginRendering: {
                surfaceId,
                root: textId
              }
            });
            messages.push({
              surfaceUpdate: {
                surfaceId,
                components: [
                  {
                    id: textId,
                    component: {
                      Text: {
                        text: { literalString: part.text }
                      }
                    }
                  }
                ]
              }
            });
          }
        }
      }
      return messages;
    }

    return [];
  }
}
