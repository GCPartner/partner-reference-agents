const http = require('http');

async function sendRequest(path, bodyStr) {
  const opts = {
    hostname: 'localhost',
    port: 8000,
    path: path,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(bodyStr)
    }
  };
  return new Promise((resolve, reject) => {
    let data = '';
    const req = http.request(opts, (res) => {
      res.on('data', c => data += c);
      res.on('end', () => resolve(data));
    });
    req.on('error', reject);
    req.write(bodyStr);
    req.end();
  });
}

function extractToolCall(streamData) {
  const lines = streamData.split('\n');
  for (let line of lines) {
    if (line.startsWith('data: ')) {
      try {
        const js = JSON.parse(line.substring(6));
        if (js.content && js.content.parts) {
          for (let part of js.content.parts) {
            if (part.functionCall) {
              return part.functionCall;
            }
          }
        }
      } catch (e) { }
    }
  }
  return null;
}

async function testAgent() {
  const appName = "phone_plan_shopper_a2ui";
  const userId = "test-user";

  // 1. Create Session
  const createResp = await sendRequest(`/apps/${appName}/users/${userId}/sessions`, JSON.stringify({ appName, userId }));
  const sessionId = JSON.parse(createResp).id || JSON.parse(createResp).sessionId;
  console.log("Created Session ID:", sessionId);

  // 2. Initial Run (User Message)
  console.log("Sending initial message...");
  let runBody = JSON.stringify({
    appName, userId, sessionId,
    newMessage: { parts: [{ text: "I need a plan with about 5GB of data." }] }
  });
  let streamResp = await sendRequest('/run_sse', runBody);

  // 3. Handle Tool Call
  const tc = extractToolCall(streamResp);
  if (tc && tc.name === "search_plans") {
    console.log("Agent requested tool:", tc.name, "with args:", tc.args);

    // Simulate tool execution
    const mockResult = {
      "plans": [
        { "plan_id": "basic_saver", "name": "Basic Saver", "data_limit": "5GB", "monthly_price": 30, "tier": "standard" }
      ]
    };

    console.log("Sending tool response...");
    runBody = JSON.stringify({
      appName, userId, sessionId,
      newMessage: {
        parts: [{
          functionResponse: {
            id: tc.id,
            name: tc.name,
            response: mockResult
          }
        }]
      }
    });
    streamResp = await sendRequest('/run_sse', runBody);
  }

  // 4. Verify Final A2UI Output
  if (streamResp.includes("a2ui_JSON") && streamResp.includes("Basic Saver")) {
    console.log("SUCCESS: A2UI JSON payload including 'Basic Saver' detected in stream.");
    process.exit(0);
  } else {
    console.error("FAILURE: A2UI response not found or did not contain expected data.");
    console.log("Stream Dump:", streamResp);
    process.exit(1);
  }
}

testAgent().catch(console.error);
