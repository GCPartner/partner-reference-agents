variable "project_id" {
  description = "The ID of the project in which to provision resources."
  type        = string
}

// Marketplace requires this variable name to be declared
variable "goog_cm_deployment_name" {
  description = "The name of the deployment."
  type        = string
}

variable "agent_engine_name" {
  description = "The name of the Agent Engine application."
  type        = string
  default     = "phone-plan-shopper"
}

variable "region" {
  description = "The GCP Region"
  type        = string
  default     = "us-central1"
}

variable "agent_package_name" {
  description = "The name of the Python package in the repo."
  type        = string
  default     = "phone_plan_shopper_db"
}

# Database Secret Variables
variable "db_conn_secret" {
  description = "Secret Manager secret ID containing the Cloud SQL instance connection name."
  type        = string
}

variable "db_user_secret" {
  description = "Secret Manager secret ID containing the Cloud SQL database user."
  type        = string
}

variable "db_pass_secret" {
  description = "Secret Manager secret ID containing the Cloud SQL database password."
  type        = string
}

variable "db_name_secret" {
  description = "Secret Manager secret ID containing the Cloud SQL database name."
  type        = string
}

# compute instance variables
variable "zone" {
  description = "The GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "machine_type" {
  description = "Machine type for the compute instance."
  type        = string
  default     = "e2-medium"
}

variable "boot_disk_size" {
  description = "Size of the boot disk (GB)."
  type        = number
  default     = 10
}

variable "boot_disk_type" {
  description = "Type of the boot disk."
  type        = string
  default     = "pd-balanced"
}

variable "source_image" {
  description = "Source image for the boot disk."
  type        = string
  default     = "projects/debian-cloud/global/images/family/debian-11"
}

variable "networks" {
  description = "List of networks to attach to."
  type        = list(string)
  default     = ["default"]
}

variable "sub_networks" {
  description = "List of sub-networks to attach to."
  type        = list(string)
  default     = []
}

variable "external_ips" {
  description = "List of external IPs (or 'NONE'/'EPHEMERAL')."
  type        = list(string)
  default     = ["EPHEMERAL"]
}

variable "enable_cloud_api" {
  description = "Enable Cloud API scope on the instance."
  type        = bool
  default     = true
}
