variable "agent_folder_name" {
  description = "The name of the folder containing the agent code"
  type        = string
  default     = "sales_data_visualizer"
}

variable "agent_engine_name" {
  description = "The display name for the Agent Engine deployment"
  type        = string
  default     = "sales-data-visualizer"
}

variable "project_id" {
  description = "The GCP Project ID"
  type        = string
  default     = "agentspace-demo-1145-b"
}

variable "region" {
  description = "The GCP Region"
  type        = string
  default     = "us-central1"
}

terraform {
  required_providers {
    google   = { source = "hashicorp/google" }
    external = { source = "hashicorp/external" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Automated Packaging & Wrapper Creation (Runs during 'terraform plan')
resource "null_resource" "pre_pack" {
  provisioner "local-exec" {
    command = "mkdir -p assets"
  }
}

data "external" "agent_packer" {
  program = ["bash", "-c", <<EOT
    set -e
    eval "$(jq -r '@sh "AGENT_FOLDER_NAME=\(.agent_folder_name)"')"
    
    AGENT_DIR=".."
    ASSETS_DIR="assets"
    ARCHIVE_PATH="$ASSETS_DIR/source.tar.gz"
    WRAPPER_PATH="$AGENT_DIR/app.py"
    
    mkdir -p "$ASSETS_DIR"

    # Create the non-intrusive wrapper app.py
    cat <<EOF > "$WRAPPER_PATH"
from vertexai.agent_engines import AdkApp
from .agent import root_agent
agent = AdkApp(agent=root_agent)
EOF

    # Build the exclusion list
    EXCLUDES=""
    EXCLUDES="$EXCLUDES --exclude=deploy"
    EXCLUDES="$EXCLUDES --exclude=.terraform"
    EXCLUDES="$EXCLUDES --exclude=.adk"
    EXCLUDES="$EXCLUDES --exclude=__pycache__"
    EXCLUDES="$EXCLUDES --exclude=*.zip"
    EXCLUDES="$EXCLUDES --exclude=*.pkl"
    EXCLUDES="$EXCLUDES --exclude=schema.json"
    EXCLUDES="$EXCLUDES --exclude=replay_test.json"
    
    if [ -f "$AGENT_DIR/.ae_ignore" ]; then
      while IFS= read -r line || [ -n "$line" ]; do
        [[ -z "$line" || "$line" =~ ^# ]] && continue
        EXCLUDES="$EXCLUDES --exclude=$line"
      done < "$AGENT_DIR/.ae_ignore"
    fi

    # Create the slim source archive
    tar -czf "$ARCHIVE_PATH" $EXCLUDES -C "$AGENT_DIR/.." "$AGENT_FOLDER_NAME/"

    echo '{"status": "ready", "archive_size": "'$(du -sh $ARCHIVE_PATH | cut -f1)'"}'
  EOT
  ]

  query = {
    agent_folder_name = var.agent_folder_name
  }

  depends_on = [null_resource.pre_pack]
}

# 2. Deployment to Agent Engine using Cloud Foundation Fabric module
module "agent_engine" {
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/agent-engine?ref=v51.0.0"
  name       = var.agent_engine_name
  project_id = var.project_id
  region     = var.region

  agent_engine_config = {
    agent_framework = "google-adk"
    environment_variables = {
      PROJECT_ID                                         = var.project_id
      LOCATION                                           = var.region
      GOOGLE_GENAI_USE_VERTEXAI                          = "1"
      GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY          = "true"
      OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT = "true"
      
      # Cloud Run Chart Service URL
      CHART_SERVICE_URL                                  = "https://chart-service-121968733869.us-central1.run.app"

      # Database connection parameters (secret_storage=file configuration)
      DB_CONNECTION_NAME                                 = "agentspace-demo-1145-b:us-central1:adk-db-3a972f08"
      DB_USER                                            = "sales_agent"
      DB_PASSWORD                                        = "1A$bLPsC3yYb*yK="
      DB_NAME                                            = "sales_consolidator_db"
    }
  }

  service_account_config = {
    roles = [
      "roles/aiplatform.user",
      "roles/cloudsql.client"
    ]
  }

  deployment_files = {
    source_config = {
      source_path       = "assets/source.tar.gz"
      entrypoint_module = "${var.agent_folder_name}.app"
      entrypoint_object = "agent"
      requirements_path = "${var.agent_folder_name}/requirements.txt"
    }
  }
  
  depends_on = [data.external.agent_packer]
}

output "reasoning_engine_id" {
  description = "The fully qualified resource ID of the deployed Agent Engine"
  value       = module.agent_engine.id
}
