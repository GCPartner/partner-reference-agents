# Phone Plan Shopper - GCS Marketplace Package

This Terraform package deploys the **Phone Plan Shopper** agent to Vertex AI Agent Engine using a pre-packaged source tarball stored in a Google Cloud Storage (GCS) bucket.

## Prerequisites

1.  **GCS Bucket**: You must have a GCS bucket containing the agent source tarball.
2.  **Source Tarball**: The tarball must contain the agent code.
    *   **Structure**: The root of the tarball should contain the package folder (e.g., `phone_plan_shopper/`).
    *   **Contents**: Inside the package folder, you must have `agent.py`, `app.py`, and `requirements.txt`.

## Preparing the Source Tarball

Run the following commands to verify and package your agent locally before uploading to GCS:

```bash
# 1. Ensure your requirements.txt is correct (Sanitize dependencies)
cat <<EOF > phone_plan_shopper/requirements.txt
google-cloud-aiplatform[agent_engines,adk]
EOF

# 2. Ensure app.py exists and uses the runtime import pattern
cat <<EOF > phone_plan_shopper/app.py
from vertexai.agent_engines import AdkApp
from .agent import root_agent
agent = AdkApp(agent=root_agent)
EOF

# 3. Create the tarball
# IMPORTANT: Tar from the parent directory so 'phone_plan_shopper/' is the top-level folder
# EXCLUDE 'deploy/' directory to avoid including large Terraform state/providers from previous runs
tar -czf source.tar.gz -C temp_source_gcs --exclude='phone_plan_shopper/deploy' phone_plan_shopper

# 4. Upload to GCS
# Replace BUCKET_NAME with your actual bucket
gsutil cp source.tar.gz gs://YOUR_BUCKET_NAME/source.tar.gz
```

## Directory Structure Requirement
The tarball **MUST** have the following structure:
```
source.tar.gz
└── phone_plan_shopper/
    ├── agent.py
    ├── app.py
    ├── requirements.txt
    └── ... other files
```
If `phone_plan_shopper/` is not the top-level folder, the deployment will fail to find `requirements.txt`.

## Deployment Inputs

| Variable | Description | Default |
|----------|-------------|---------|
| `project_id` | The GCP Project ID | Required |
| `gcs_source_bucket` | The GCS bucket name (e.g. `my-agent-bucket`) | Required |
| `source_archive_path` | Path to the file in the bucket (e.g. `source.tar.gz`) | `source.tar.gz` |
| `agent_engine_name` | Name of the agent application | `phone-plan-shopper` |
| `region` | GCP Region | `us-central1` |

## Observability

This package automatically enables the following observability features for the deployed agent:
*   `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`: `true`
*   `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`: `true`

This ensures that traces and logs (including message content) are captured in Google Cloud Trace and Cloud Logging.

## Local Testing

1.  Create a `testing.tfvars` file:
    ```hcl
    project_id          = "your-project-id"
    goog_cm_deployment_name = "test-deploy"
    gcs_source_bucket   = "your-bucket-name"
    ```

2.  Initialize and Plan:
    ```bash
    terraform init
    terraform plan -var-file="testing.tfvars"
    ```
