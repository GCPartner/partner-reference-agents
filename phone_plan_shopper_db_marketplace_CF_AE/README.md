# Phone Plan Shopper (DB-Backed) - Marketplace Package

This package allows you to deploy the **Phone Plan Shopper (Database Edition)** agent to **Vertex AI Agent Engine** via Google Cloud Marketplace (using Terraform). This version of the agent fetches live plan and device data from a Cloud SQL PostgreSQL database instead of using mocked data.

## Overview

This Terraform configuration:
1.  **Packages** the agent code from the local `../phone_plan_shopper_db` directory (configurable via script).
2.  **Deploys** the agent to Vertex AI Agent Engine using the Google Cloud Foundation Fabric module.
3.  **Configures** the agent's environment variables to read database connection info from Secret Manager.
4.  **Authorizes** the agent's service account to access Secret Manager (`roles/secretmanager.secretAccessor`).

## Database Preparation (Required Before Deployment)

This agent **requires** a Google Cloud SQL PostgreSQL database to be provisioned *before* you deploy the agent. 

Follow these steps to set up the database and securely store its credentials in Secret Manager:

1.  **Provision Cloud SQL**:
    Create a new PostgreSQL instance in your Google Cloud Project.
    ```bash
    # Set your project and region
    PROJECT_ID="<YOUR_PROJECT_ID>"
    REGION="us-central1" 
    INSTANCE_NAME="phone-plan-db"

    # Create the Cloud SQL PostgreSQL instance (this takes a few minutes)
    gcloud sql instances create $INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --cpu=1 --memory=4GB \
        --region=$REGION \
        --project=$PROJECT_ID
    ```
2.  **Create Database & User**:
    Create a database (e.g., `phone_plan_shopper`) and a user with a strong password.
    ```bash
    DB_NAME="phone_plan_shopper"
    DB_USER="phone_plan_user"
    DB_PASS="<STRONG_PASSWORD>"

    # Create the database
    gcloud sql databases create $DB_NAME \
        --instance=$INSTANCE_NAME \
        --project=$PROJECT_ID

    # Create the user
    gcloud sql users create $DB_USER \
        --instance=$INSTANCE_NAME \
        --password=$DB_PASS \
        --project=$PROJECT_ID
    ```
3.  **Create Secrets in Secret Manager**:
    Instead of passing plaintext credentials, the agent dynamically fetches them from Secret Manager. You **must** create the following 4 secrets in your Google Cloud Project:
    ```bash
    # Ensure Secret Manager API is enabled
    gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID

    # 1. Instance Connection Name (Format: project-id:region:instance-name)
    CONNECTION_NAME="$PROJECT_ID:$REGION:$INSTANCE_NAME"
    echo -n "$CONNECTION_NAME" | gcloud secrets create phone_plan_db_connection_name \
        --data-file=- --project=$PROJECT_ID

    # 2. Database User
    echo -n "$DB_USER" | gcloud secrets create phone_plan_db_user \
        --data-file=- --project=$PROJECT_ID

    # 3. Database Password
    echo -n "$DB_PASS" | gcloud secrets create phone_plan_db_password \
        --data-file=- --project=$PROJECT_ID

    # 4. Database Name
    echo -n "$DB_NAME" | gcloud secrets create phone_plan_db_name \
        --data-file=- --project=$PROJECT_ID
    ```
4.  **Initialize Data**: Ensure the `plans` and `devices` tables are created and populated with data. (You can run `db_init.py` from the origin source to handle this).

*Note: During Marketplace deployment, you will be prompted to enter the **names** of the secrets you created above, NOT the actual credentials.*

## Prerequisites

- A Google Cloud Project with billing enabled.
- Python 3 to run the packaging script.
- The following APIs enabled (handled by the module, but good to know):
    - `aiplatform.googleapis.com`
    - `compute.googleapis.com`
    - `storage.googleapis.com`
    - `secretmanager.googleapis.com`
    - `sqladmin.googleapis.com`

### Marketplace Deployment Service Account Permissions

When configuring the deployment in the Google Cloud Marketplace UI, you will be asked to select a **Deployment Service Account**. 

This Service Account **MUST** have the following roles granted to it at the Project level:
1. `roles/owner` or `roles/editor` (Typical for creating resources like Vertex AI Reasoning Engines and VMs).
2. **`roles/iam.serviceAccountUser` (Service Account User):** This is CRITICAL. The deployment creates a new Service Account for the Agent Engine and attaches the default service account to a reporting Compute VM. It cannot attach these service accounts without the `iam.serviceAccountUser` role. If you see an error stating *"The user does not have access to service account..."*, it means your deployment service account is missing this specific role.

## Inputs

| Name | Description | Default |
|------|-------------|---------|
| `project_id` | GCP Project ID | (Required) |
| `goog_cm_deployment_name` | Deployment Name (Marketplace convention) | (Required) |
| `agent_engine_name` | Name of the Agent Engine app | `phone-plan-shopper` |
| `region` | GCP Region | `us-central1` |
| `agent_package_name` | Python package name | `phone_plan_shopper_db` |
| `db_conn_secret` | Secret Name for Cloud SQL Connection Name | (Required) |
| `db_user_secret` | Secret Name for Database User | (Required) |
| `db_pass_secret` | Secret Name for Database Password | (Required) |
| `db_name_secret` | Secret Name for Database Name | (Required) |

## Outputs

- `agent_engine_id`: The unique ID of the deployed Agent Engine application.
- `agent_name`: The name of the agent.

## Local Testing

You can test this configuration locally using the `marketplace_test.tfvars` file (create one if needed):

```bash
# 1. Package the agent
python3 package_agent.py --source ../phone_plan_shopper_db

# 2. Initialize Terraform
terraform init

# 3. Plan deployment (Replace with your actual Secret Manager secret names)
terraform plan \
  -var "project_id=YOUR_PROJECT_ID" \
  -var "goog_cm_deployment_name=test-deploy" \
  -var "db_conn_secret=phone_plan_db_connection_name_secret" \
  -var "db_user_secret=phone_plan_db_user_secret" \
  -var "db_pass_secret=phone_plan_db_password_secret" \
  -var "db_name_secret=phone_plan_db_name_secret"

# 4. Apply
terraform apply \
  ... (same flags as plan)
```
