# How to Package an ADK Agent for GCS Marketplace Deployment

This guide explains how to prepare any ADK agent for deployment to Vertex AI Agent Engine using the GCS-based `package_spec` method. This method eliminates the need for complex local download scripts during Terraform execution.

## Prerequisites

1.  **Python 3.10+** installed.
2.  **Google Cloud SDK (`gcloud`)** installed and authenticated.
3.  **Python Dependencies**:
    ```bash
    pip install cloudpickle google-cloud-storage
    ```
4.  **Agent Source Code**: Your agent should be structured as a valid Python package.
5.  **(Optional) `.ae_ignore`**: Create a `.ae_ignore` file in your source root to exclude specific files/directories (syntax similar to `.gitignore`). `.env` is always excluded by default.

## The Helper Script (`generic_package_for_gcs.py`)

A reusable script `generic_package_for_gcs.py` is provided to automate the packaging process. It performs three key steps:
1.  **Pickles the Agent**: Imports your agent object and serializes it using `cloudpickle`.
2.  **Packages Source**: Creates a tarball (`dependencies.tar.gz`) of your agent's source code.
3.  **Packages Requirements**: Copies `requirements.txt`.
4.  **Uploads to GCS**: Uploads all three artifacts to your specified bucket.

### Usage

```bash
python3 generic_package_for_gcs.py \
  --agent-src-dir <ABS_PATH_TO_SOURCE_ROOT> \
  --import-module <PYTHON_MODULE_PATH> \
  --agent-var <VARIABLE_NAME> \
  --project <GCP_PROJECT_ID> \
  --bucket <GCS_BUCKET_NAME> \
  --prefix <OPTIONAL_PREFIX>
```

### Arguments

| Argument | Description | Example |
| :--- | :--- | :--- |
| `--agent-src-dir` | Absolute path to the directory containing your agent's package and `requirements.txt`. | `/home/user/code/my_agent_repo` |
| `--import-module` | The Python import path to the file containing your agent object. | `my_agent.app` |
| `--agent-var` | The name of the variable holding the `AdkApp` or `ReasoningEngine` object. | `agent` (default) |
| `--project` | Your Google Cloud Project ID. | `my-project-id` |
| `--bucket` | The GCS bucket where artifacts will be uploaded. | `my-agent-artifacts` |
| `--prefix` | (Optional) Folder prefix within the bucket. | `prod/v1` |

## Example: Packaging `phone_plan_shopper`

Assuming your directory structure is:
```
/usr/local/google/home/veermuchandi/code/agents/rad-workshop/phone_plan_shopper/
├── requirements.txt
└── phone_plan_shopper/
    ├── __init__.py
    └── app.py  <-- contains 'agent = ...'
```

Run the script:

```bash
python3 generic_package_for_gcs.py \
  --agent-src-dir /usr/local/google/home/veermuchandi/code/agents/rad-workshop/phone_plan_shopper \
  --import-module phone_plan_shopper.app \
  --agent-var agent \
  --project partner-engg-agents \
  --bucket phone-plan-shopper-source-test-veermuchandi \
  --prefix agent-package
```

## Terraform Integration

Once the artifacts are uploaded, update your `terraform.tfvars` (or `testing.tfvars`) with the GCS URIs output by the script:

```hcl
pickle_object_gcs_uri    = "gs://your-bucket/prefix/agent.pkl"
requirements_gcs_uri     = "gs://your-bucket/prefix/requirements.txt"
dependency_files_gcs_uri = "gs://your-bucket/prefix/dependencies.tar.gz"
```

These values are passed to the `google_vertex_ai_reasoning_engine` resource in your `main.tf`.
