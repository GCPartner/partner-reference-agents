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

# 1. Deployment to Agent Engine using Cloud Foundation Fabric module
module "agent_engine" {
  # ORIGINAL (GitHub Source) - Requires Terraform >= 1.12.2
  # source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/agent-engine?ref=v51.0.0"

  # LOCAL VENDORING (Relaxed Constraint >= 1.5.7)
  source     = "./modules/agent-engine"
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
      DB_CONN_SECRET                                     = var.db_conn_secret
      DB_USER_SECRET                                     = var.db_user_secret
      DB_PASS_SECRET                                     = var.db_pass_secret
      DB_NAME_SECRET                                     = var.db_name_secret
    }
  }

  service_account_config = {
    create = true
    roles = [
      "roles/aiplatform.user",
      "roles/storage.objectViewer",
      "roles/viewer",
      "roles/serviceusage.serviceUsageConsumer",
      "roles/cloudtrace.agent",
      "roles/secretmanager.secretAccessor",
    ]
  }

  deployment_files = {
    source_config = {
      source_path       = "assets/source.tar.gz"
      entrypoint_module = "${var.agent_package_name}.app"
      entrypoint_object = "agent"
      requirements_path = "${var.agent_package_name}/requirements.txt"
    }
  }
}

#Compute Instance
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

