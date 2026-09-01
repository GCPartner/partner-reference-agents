# App in Iframe (A2UI v0.9 Agent)

An Agent-Driven User Interface (A2UI) agent that prompts users for a web application URL and embeds it inside an interactive side-panel `Canvas` using the A2UI v0.9 `IFrameUrl` component.

---

## Features

- **A2UI v0.9 Compliant**: Implements the canonical flat schema with `createSurface`, `updateComponents`, and `updateDataModel`.
- **Canvas Side-Panel Integration**: Uses `Canvas` as the root component (`autoOpen: true`) for side-panel preview.
- **Interactive Intake Form**: Renders a Material card with `MaterialInput` and `MaterialButton` to request and validate web application URLs.
- **Robust URL Extraction**: Sanitizes URLs from raw input, bracketed text, and Markdown link formats (`[https://...](https://...)`).
- **Cloud Run & A2A Compatible**: Includes native Starlette ASGI server with `/healthz` endpoints and `/a2a/app_in_iframe_a2ui` protocol routing.

---

## Project Structure

```text
app_in_iframe_a2ui/
├── .env.example                     # Environment template
├── .gitignore                       # Repository ignore rules
├── README.md                        # Documentation
├── agent.json                       # A2A agent configuration
├── agent.py                         # Root LlmAgent definition & instructions
├── agent_architecture.md            # Architectural design document
├── agent_executor.py                # A2UI stream parser & DataPart converter
├── common_types_v0_9.json           # A2UI common types schema
├── composite_catalog_v0_9.json      # Gemini Enterprise Composite Catalog schema
├── design/                          # UI design wireframes
├── requirements.txt                 # Dependencies
├── server.py                        # Starlette ASGI server for Cloud Run
├── sitecustomize.py                 # Protocol serialization patches
├── test_agent.py                    # Multi-turn local test harness
└── tools.py                         # Intake UI & IFrameUrl renderer tools
```

---

## Quickstart (Local Testing)

1. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Multi-Turn Verification Harness**:
   ```bash
   python3 test_agent.py
   ```

---

## Deployment to Cloud Run

Deploy using the automated A2UI Cloud Run Deployer:

```bash
python3 -m deploy_a2ui \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --agent_dir ./app_in_iframe_a2ui \
  --service_name app-in-iframe-a2ui
```

Once deployed, register the A2A endpoint (`https://YOUR_SERVICE_URL/a2a/app_in_iframe_a2ui`) with your Gemini Enterprise application.
