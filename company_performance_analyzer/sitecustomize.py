import os
import json

print("[SITECUSTOMIZE] Python startup customization script triggered!")

# Save project parameters to a temporary JSON file to retrieve them later in agent_wrapper
env_data = {
    "PROJECT_ID": os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT"),
    "LOCATION": os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
}

try:
    with open("/tmp/saved_env.json", "w") as f:
        json.dump(env_data, f)
    print(f"[SITECUSTOMIZE] Stashed environment parameters: {env_data}")
except Exception as e:
    print(f"[SITECUSTOMIZE] Failed to stash environment parameters: {e}")

# Strip all offending environment variables to bypass strict Settings validation in the base container
for key in [
    "GEMINI_ENTERPRISE_APP_ID",
    "STORAGE_BUCKET",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
    "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY",
    "PROJECT_ID",
    "LOCATION",
    "GOOGLE_GENAI_USE_VERTEXAI"
]:
    val = os.environ.pop(key, None)
    val_lower = os.environ.pop(key.lower(), None)
    if val or val_lower:
        print(f"[SITECUSTOMIZE] Unset environment key: {key}")

print("[SITECUSTOMIZE] Environment cleanup complete.")
