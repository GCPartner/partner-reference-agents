/**
 * # Agent Engine Deployment from GCS (Package Spec)
 *
 * This configuration deploys an ADK agent to Vertex AI Agent Engine using pre-packaged artifacts in GCS.
 */

provider "google" {
  project = var.project_id
}

locals {
  # Clean agent name to be used for resource naming (standardize)
  agent_name_clean  = replace(var.agent_engine_name, "_", "-")
}

# 1. Create Service Account for the Agent
resource "google_service_account" "agent_sa" {
  account_id   = local.agent_name_clean
  display_name = "Service Account for ${var.agent_engine_name}"
  project      = var.project_id
}

# 2. Grant IAM Roles to the Service Account
# We use a set of roles required for typical ADK agents
locals {
  agent_roles = [
    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectViewer",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent"
  ]
}

resource "google_project_iam_member" "agent_roles" {
  for_each = toset(local.agent_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.agent_sa.email}"
}

# 3. Deploy Reasoning Engine using package_spec
resource "google_vertex_ai_reasoning_engine" "managed" {
  provider = google-beta
  display_name = var.agent_engine_name
  description  = "Deployed from package artifacts in GCS"
  project      = var.project_id
  region       = var.region

  spec {
    deployment_spec {
      # Service account config not supported in this provider version
      # service_account_email = google_service_account.agent_sa.email
      env {
        name  = "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"
        value = "true"
      }
      env {
        name  = "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"
        value = "true"
      }
      env {
        name = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "true"
      }
    }
    
    package_spec {
        pickle_object_gcs_uri    = var.pickle_object_gcs_uri
        dependency_files_gcs_uri = var.dependency_files_gcs_uri
        requirements_gcs_uri     = var.requirements_gcs_uri
        python_version           = "3.12"
    }
  }

  # Ensure IAM is ready before deployment
  depends_on = [google_project_iam_member.agent_roles]
}
