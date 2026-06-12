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

locals {
  network_interfaces = [ for i, n in var.networks : {
    network     = n,
    subnetwork  = length(var.sub_networks) > i ? element(var.sub_networks, i) : null
    external_ip = length(var.external_ips) > i ? element(var.external_ips, i) : "NONE"
    }
  ]

  metadata = {
    google-logging-enable = "0"
    google-monitoring-enable = "0"
  }
}

resource "google_compute_instance" "instance" {
  name = "${var.goog_cm_deployment_name}-vm"
  machine_type = var.machine_type
  zone = var.zone

  tags = ["${var.goog_cm_deployment_name}-deployment"]

  boot_disk {
    device_name = "autogen-vm-tmpl-boot-disk"

    initialize_params {
      size = var.boot_disk_size
      type = var.boot_disk_type
      image = var.source_image
    }
  }

  metadata = local.metadata

  dynamic "network_interface" {
    for_each = local.network_interfaces
    content {
      network = network_interface.value.network
      subnetwork = network_interface.value.subnetwork

      dynamic "access_config" {
        for_each = network_interface.value.external_ip == "NONE" ? [] : [1]
        content {
          nat_ip = network_interface.value.external_ip == "EPHEMERAL" ? null : network_interface.value.external_ip
        }
      }
    }
  }

  service_account {
    email = "default"
    scopes = compact([
      "https://www.googleapis.com/auth/cloud.useraccounts.readonly",
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring.write"
      ,var.enable_cloud_api == true ? "https://www.googleapis.com/auth/cloud-platform" : null
    ])
  }
}
