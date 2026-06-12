variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
}
// Marketplace requires this variable name to be declared
variable "goog_cm_deployment_name" {
  description = "The name of the deployment and VM instance."
  type        = string
}

variable "source_image" {
  description = "The image name for the disk for the VM instance."
  type        = string
  default     = "projects/cpe-isv-partner-experiments/global/images/gsi-agent-test-image"
}

variable "region" {
  description = "The Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "agent_engine_name" {
  description = "The name of the Agent Engine to create"
  type        = string
  default     = "my-agent"
}

variable "pickle_object_gcs_uri" {
    description = "GCS URI for the pickled agent object (agent.pkl)"
    type        = string
    default     = "gs://replace-your-bucket-name/agent.pkl"
}

variable "requirements_gcs_uri" {
    description = "GCS URI for the requirements.txt file"
    type        = string
    default     = "gs://replace-your-bucket-name/requirements.txt"
}

variable "dependency_files_gcs_uri" {
    description = "GCS URI for the dependencies.tar.gz file"
    type        = string
    default     = "gs://replace-your-bucket-name/dependencies.tar.gz"
}


variable "zone" {
  description = "The zone for the solution to be deployed."
  type        = string
  default     = "us-central1-a"
}

variable "machine_type" {
  description = "The machine type to create, e.g. e2-small"
  type        = string
  default     = "f1-micro"
}

variable "boot_disk_type" {
  description = "The boot disk type for the VM instance."
  type        = string
  default     = "pd-standard"
}

variable "boot_disk_size" {
  description = "The boot disk size for the VM instance in GBs"
  type        = number
  default     = 10
}

variable "networks" {
  description = "The network name to attach the VM instance."
  type        = list(string)
  default     = ["default"]
}

variable "sub_networks" {
  description = "The sub network name to attach the VM instance."
  type        = list(string)
  default     = []
}

variable "external_ips" {
  description = "The external IPs assigned to the VM for public access."
  type        = list(string)
  default     = ["EPHEMERAL"]
}

variable "enable_cloud_api" {
  description = "Allow full access to all of Google Cloud Platform APIs on the VM"
  type        = bool
  default     = true
}
