# Phone Plan Shopper - Marketplace Package

This package allows you to deploy the **Phone Plan Shopper** agent to **Vertex AI Agent Engine** via Google Cloud Marketplace (using Terraform).

## Overview

This Terraform configuration:
1.  **Packages** the agent code from the local `../phone_plan_shopper` directory (configurable via script).
2.  **Deploys** the agent to Vertex AI Agent Engine using the Google Cloud Foundation Fabric module.

## Prerequisites

- A Google Cloud Project with billing enabled.
- Python 3 to run the packaging script.
- The following APIs enabled (handled by the module, but good to know):
    - `aiplatform.googleapis.com`
    - `compute.googleapis.com`
    - `storage.googleapis.com`

## Inputs

| Name | Description | Default |
|------|-------------|---------|
| `project_id` | GCP Project ID | (Required) |
| `goog_cm_deployment_name` | Deployment Name (Marketplace convention) | (Required) |
| `agent_engine_name` | Name of the Agent Engine app | `phone-plan-shopper` |
| `region` | GCP Region | `us-central1` |
| `agent_package_name` | Python package name | `phone_plan_shopper` |

## Outputs

- `agent_engine_id`: The unique ID of the deployed Agent Engine application.
- `agent_name`: The name of the agent.

## Local Testing

You can test this configuration locally using the `marketplace_test.tfvars` file (create one if needed):

```bash
# 1. Package the agent
python3 package_agent.py --source ../phone_plan_shopper

# 2. Initialize Terraform
terraform init

# 3. Plan deployment
terraform plan -var "project_id=YOUR_PROJECT_ID" -var "goog_cm_deployment_name=test-deploy"

# 4. Apply
terraform apply -var "project_id=YOUR_PROJECT_ID" -var "goog_cm_deployment_name=test-deploy"
```
