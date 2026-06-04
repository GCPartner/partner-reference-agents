# A2UI Testing & Deployment Lessons Learned

This document outlines key discoveries, implementation details, and troubleshooting steps for deploying and testing A2UI agents on Vertex AI Agent Engine.

---

## 1. Unified Origin for Mock Client & API
* **Problem**: Running the mock client (e.g., port 8080) and the FastAPI server (port 8000) on separate ports causes the browser to issue CORS preflight (`OPTIONS`) requests. In remote VM/SSH environments behind proxy redirection, these preflight requests are often intercepted or blocked, causing API connection failures.
* **Solution**: Serve the mock client directly from the FastAPI server root `/` endpoint (using FastAPI's `FileResponse` to return `index.html`). This guarantees both the client and the JSON-RPC endpoints share a unified origin (e.g., `http://localhost:8000/`) and avoids CORS entirely.

---

## 2. A2A Protocol and DataPart Nesting
* **Problem**: In A2A protocol `v0.8` (REST wrapper), sending actions or data payloads in `message.content` using `DataPart` requires strict nesting. The REST message parser maps the JSON structure to a protobuf schema:
  - `Part` has a `data` field of type `DataPart`.
  - `DataPart` has a `data` field of type `google.protobuf.Struct`.
  - If you forward `a2a_part["data"] = part["data"]` directly (which contains keys like `userAction`), the parser fails with `Message type "a2a.v1.DataPart" has no field named "userAction"`.
* **Solution**: Wrap the incoming action payload inside a nested `"data"` key in the proxy server mapping:
  ```python
  if "data" in part:
      a2a_part["data"] = {"data": part["data"]}
  ```
  And when returning the task artifacts to the client, flatten it:
  ```python
  if "data" in part and part.get("metadata", {}).get("mimeType") == "application/json+a2ui":
      data_field = part["data"]
      if isinstance(data_field, dict) and "data" in data_field:
          part["data"] = data_field["data"]
  ```

---

## 3. Protobuf Enum Case Sensitivity
* **Problem**: The A2A API REST endpoint is strictly bound to protobuf schemas. When defining the `role` field on a message sent to the agent engine, using `"role": "USER"` fails with `ParseError: Invalid enum value USER for enum type a2a.v1.Role`.
* **Solution**: Use the exact case-sensitive enum definition name expected by the compiled protobuf description:
  - `"role": "ROLE_USER"` (instead of `"USER"`)
  - `"role": "ROLE_AGENT"` (instead of `"AGENT"`)

---

## 4. Preventing `SessionNotFoundError` in Deployed Container Runtimes
* **Problem**: When running on hosted Google Cloud runtime environments (where containers may scale down or recycle), the default ADK runner throws `SessionNotFoundError: Session not found` when a request arrives with a new session ID, or if the container is recycled and the in-memory session store is cleared.
* **Solution**: Configure the `runners.Runner` with `auto_create_session=True` in `agent_executor.py`:
  ```python
  self._runner = runners.Runner(
      app_name="A2UIAgent",
      agent=root_agent,
      session_service=in_memory_session_service.InMemorySessionService(),
      auto_create_session=True,  # Automatically initializes missing sessions
  )
  ```

---

## 5. Adjusting Browser Test Timeouts for Cold Starts
* **Problem**: Headless browser automation (e.g. Playwright) has a default wait timeout of 30 seconds. A freshly updated or scaled-down Agent Engine reasoning engine container can require up to 40-50 seconds to complete its initial cold start and process the first tool execution.
* **Solution**: Set explicit wait timeouts on the initial greeting response selector in your Playwright script:
  ```python
  await page.wait_for_selector('[id="/trip/start_location_input"]', timeout=90000)
  ```
