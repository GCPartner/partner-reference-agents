# How to Package Agent Source Code

This guide explains how to package the `phone_plan_shopper` agent source code for deployment to Vertex AI Agent Engine using the provided `package_agent.py` script.

## Overview

Vertex AI Agent Engine requires the agent source code to be packaged in a specific format (tar.gz) with an entry point (`app.py`) and a `requirements.txt` file compatible with the runtime environment.

The `package_agent.py` script automates this process by:
1.  Copying the agent source code to a temporary directory.
2.  Creating a wrapper `app.py` that initializes the agent.
3.  Generating a `requirements.txt` file with the necessary dependencies.
4.  Creating a `.tar.gz` archive ready for deployment.
5.  Generating `agent_config.auto.tfvars` with the correct `agent_package_name` variable so Terraform can deploy without manual input.

## Prerequisites

-   Python 3 installed.
-   Access to the agent source code directory.

## Usage

Run the script from the `phone_plan_shopper_marketplace` directory:

```bash
python3 package_agent.py --source <path_to_agent_source>
```

### Arguments

-   `--source`: (Required) Path to the agent source directory (e.g., `../phone_plan_shopper`).
-   `--output`: (Optional) Path to the output tar.gz file. Defaults to `assets/source.tar.gz`.
-   `--package-name`: (Optional) Name of the Python package. Defaults to the basename of the source directory (e.g., `phone_plan_shopper`).

### Example

To package the agent using the default settings:

```bash
python3 package_agent.py --source ../phone_plan_shopper
```

This will create `assets/source.tar.gz`.

## Integration with Terraform

The `main.tf` Terraform configuration is set up to look for the packaged source at `assets/source.tar.gz`.

### Automatic Configuration (`agent_package_name`)

To avoid manual configuration errors, the `package_agent.py` script automatically generates a file named `agent_config.auto.tfvars` in the same directory. This file contains the `agent_package_name` variable, which matches the folder name you packaged (or the name you specified with `--package-name`).

**Example `agent_config.auto.tfvars`:**
```hcl
agent_package_name = "phone_plan_shopper"
```

Terraform automatically loads any file ending in `.auto.tfvars`, ensuring that the `agent_package_name` variable is always set correctly for deployment.

**Important:** You must run this packaging script *before* running `terraform apply` or `terraform plan`.

**Important:** You must run this packaging script *before* running `terraform apply` or `terraform plan`.

## What's Included in the Package?

The script packages the following:
-   The entire agent source directory (excluding `.git`, `.venv`, `__pycache__`, etc.).
-   A generated `app.py` (entry point).
-   A generated `requirements.txt`.

The resulting archive structure looks like this:

```
source.tar.gz
└── phone_plan_shopper/
    ├── agent.py
    ├── tools.py
    ├── ... (other source files)
    ├── app.py          <-- Generated
    └── requirements.txt <-- Generated
```

## Preparing for Marketplace

To deploy this agent via Google Cloud Marketplace, you need to bundle the configuration files into a zip archive.

**Important:** You **MUST** include the `modules/` directory in this archive, as it contains the required Terraform module dependencies.

**Run this command to create the package:**

```bash
zip -r phone_plan_shopper.zip \
  main.tf \
  metadata.display.yaml \
  metadata.yaml \
  outputs.tf \
  README.md \
  variables.tf \
  marketplace_test.tfvars \
  agent_config.auto.tfvars \
  assets/source.tar.gz \
  modules/
```
