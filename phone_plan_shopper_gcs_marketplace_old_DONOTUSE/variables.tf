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
