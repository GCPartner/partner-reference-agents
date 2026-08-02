# CareConnect Navigator (Canvas A2UI)

An intelligent, empathetic healthcare navigator agent built using the Google Agent Development Kit (ADK) and the **A2UI Protocol (v0.9)**. It provides a split-screen experience in Gemini Enterprise: interactive chat on the left, and a persistent appointment booking wizard on the right.

## Features & Wizard Steps
1. **Insurance Plan Selection**: HMO / PPO selection.
2. **Search Criteria Selection**: Specialty (e.g. Pediatrics, Dermatology) and Zip Code inputs.
3. **Provider Selection**: Side-by-side card layout showing doctor photos (served from Cloud Storage), specialties, network status, and Out-of-Network warning alerts.
4. **Appointment Slot Selection**: Time slot buttons check.
5. **Review & Book**: Appointment details summary.
6. **Booking Confirmation**: Renders the final confirmation ID.

## Core Design Patterns Used
*   **Single Persistent Surface**: Uses a single surface ID (`"navigator"`) and updates components in-place using `updateComponents` and `updateDataModel`. This prevents side-panel flickering or teardowns.
*   **State Preservation**: Dynamically syncs the data model values on forward/backward navigation to pre-populate selection states.

## Getting Started

### Prerequisites
*   Python 3.11+
*   Terraform 1.14+
*   Google Cloud Platform (GCP) credentials set up.

### Environment Setup
1. Copy the environment variables template and configure it:
    ```bash
    cp .env.example .env
    ```
2. Copy the Terraform variables template:
    ```bash
    cp deploy/terraform.tfvars.template deploy/terraform.tfvars
    ```

### Local Testing
To test the agent flow locally using the mock A2A JSON-RPC client:
1. Install dependencies:
    ```bash
    pip3 install -r requirements.txt
    ```
2. Start the local mock server:
    ```bash
    python3 local_tester/server.py
    ```

### Deployment to Vertex AI Agent Engine
Deploys the agent packaging automatically and provisions the required GCS assets bucket:
```bash
cd deploy
terraform init
terraform apply -auto-approve
```
Once deployed, copy the Reasoning Engine ID and update the `registration_payload.json` using the template.

### Registration in Gemini Enterprise
Register the agent using the registrar helper tool with the active Reasoning Engine URL and Authorization config.
