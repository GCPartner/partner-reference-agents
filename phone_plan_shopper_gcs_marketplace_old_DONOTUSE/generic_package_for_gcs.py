
import os
import sys
import argparse
import tarfile
import cloudpickle
import importlib.util
from google.cloud import storage

def package_and_upload(agent_src_dir, import_module, agent_var, project_id, bucket_name, prefix=""):
    """
    Packages any ADK agent and uploads artifacts to GCS.
    
    Args:
        agent_src_dir: Absolute path to the directory containing the agent code (parent of the module).
        import_module: Dot-separated python module path (e.g., 'my_agent.app').
        agent_var: Name of the agent object variable in the module (e.g., 'agent').
        project_id: GCP Project ID.
        bucket_name: GCS Bucket Name.
        prefix: GCS Object Prefix.
    """
    agent_src_dir = os.path.abspath(agent_src_dir)
    if not os.path.exists(agent_src_dir):
        print(f"Error: Agent source directory not found at {agent_src_dir}")
        sys.exit(1)

    # Temporary build directory
    build_dir = os.path.join(os.getcwd(), "build_artifacts_generic")
    os.makedirs(build_dir, exist_ok=True)

    pickle_path = os.path.join(build_dir, "agent.pkl")
    reqs_path = os.path.join(build_dir, "requirements.txt")
    deps_path = os.path.join(build_dir, "dependencies.tar.gz")

    print(f"Packaging agent from {agent_src_dir}...")

    # 1. Pickle the Agent
    try:
        # Add parent of agent_src_dir to sys.path so we can import the module if it's a package
        # However, usually agent_src_dir IS the package root. 
        # Example: if module is 'phone_plan_shopper.app', we expect 'phone_plan_shopper' directory inside 'agent_src_dir'?
        # OR agent_src_dir IS the 'phone_plan_shopper' dir?
        # Let's assume agent_src_dir contains the package. 
        # Wait, usually for 'phone_plan_shopper.app', we need the parent of 'phone_plan_shopper' in path.
        
        # Let's rely on the user providing the correct generic path structure.
        # Best practice: agent_src_dir is the repo root, containing requirements.txt and the python package.
        
        # Add parent of agent_src_dir to sys.path so we can import the module if it's a package
        sys.path.insert(0, os.path.dirname(agent_src_dir))
        sys.path.insert(0, agent_src_dir)
        
        # Dynamic import
        spec = importlib.util.find_spec(import_module)
        if spec is None:
             print(f"Error: Module {import_module} not found in {agent_src_dir}")
             sys.exit(1)
             
        module = importlib.util.module_from_spec(spec)
        sys.modules[import_module] = module
        spec.loader.exec_module(module)
        
        agent_obj = getattr(module, agent_var)
        
        with open(pickle_path, "wb") as f:
            cloudpickle.dump(agent_obj, f)
        print(f"Generated {pickle_path}")
        
    except Exception as e:
        print(f"Error pickling agent: {e}")
        # print stack trace for debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 2. Prepare requirements.txt
    source_reqs = os.path.join(agent_src_dir, "requirements.txt")
    if os.path.exists(source_reqs):
        with open(source_reqs, "r") as src, open(reqs_path, "w") as dst:
            dst.write(src.read())
        print(f"Generated {reqs_path}")
    else:
        print(f"Warning: No requirements.txt found at {source_reqs}. Creating minimal.")
        with open(reqs_path, "w") as f:
            f.write("google-adk>=0.1.0\n") 

    # 3. Create dependencies.tar.gz
    # We want to tar the python package(s) inside agent_src_dir.
    # To be safe, we tar the entire content of agent_src_dir, excluding hidden files and build artifacts.
    # But usually we only want the python package code.
    # Let's inspect the top-level module name from import_module.
    top_level_package = import_module.split('.')[0]
    package_path = os.path.join(agent_src_dir, top_level_package)
    
    # Parse .ae_ignore (or fallback to .gitignore if you wanted, but user asked for .ae_ignore)
    ignore_patterns = []
    ae_ignore_path = os.path.join(agent_src_dir, ".ae_ignore")
    if os.path.exists(ae_ignore_path):
        print(f"Found .ae_ignore at {ae_ignore_path}")
        with open(ae_ignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ignore_patterns.append(line)
    
    # Always ensure .env and hidden files/dirs that are crucial to ignore are added if not present
    # But user might want some hidden files. Let's stick to .ae_ignore + .env mandatory.
    if ".env" not in ignore_patterns:
        ignore_patterns.append(".env")

    import fnmatch

    def exclude_filter(tarinfo):
        # tarinfo.name is relative to the archive root (e.g., "phone_plan_shopper/app.py")
        # We need to match against patterns. 
        # Patterns like "*.json" should match "phone_plan_shopper/replay.json".
        # Patterns like "deploy/" should match "phone_plan_shopper/deploy".
        
        # Simple fnmatch implementation for now.
        basename = os.path.basename(tarinfo.name)
        
        # Check against all ignore patterns
        for pattern in ignore_patterns:
            # Handle directory matches (if pattern ends with /)
            if pattern.endswith("/"):
                # strict directory check might be hard with tarinfo, let's just strip /
                clean_pattern = pattern.rstrip("/")
                if fnmatch.fnmatch(basename, clean_pattern) and tarinfo.isdir():
                    return None
                if fnmatch.fnmatch(tarinfo.name, f"*/{clean_pattern}") and tarinfo.isdir():
                    return None
            
            # Handle standard wildcards
            if fnmatch.fnmatch(basename, pattern):
                return None
            
            # recursive path matching (simplified)
            # if user ignores "deploy", we should ignore "phone_plan_shopper/deploy"
            if f"/{pattern}" in tarinfo.name or tarinfo.name.endswith(f"/{pattern}"):
                 return None
                 
        return tarinfo

    with tarfile.open(deps_path, "w:gz") as tar:
        if os.path.exists(package_path):
            tar.add(package_path, arcname=top_level_package, filter=exclude_filter)
            print(f"Added {top_level_package} to archive (filtered by .ae_ignore)")
        else:
             print(f"Warning: Could not find package directory {package_path}. Tarring entire src dir as {top_level_package}.")
             tar.add(agent_src_dir, arcname=top_level_package, filter=exclude_filter)

    print(f"Generated {deps_path}")

    # 4. Upload to GCS
    if bucket_name:
        print(f"Uploading to gs://{bucket_name}/{prefix}...")
        try:
            storage_client = storage.Client(project=project_id)
            bucket = storage_client.bucket(bucket_name)

            artifacts = {
                "agent.pkl": pickle_path,
                "requirements.txt": reqs_path,
                "dependencies.tar.gz": deps_path
            }

            uploaded_uris = {}

            for blob_name, local_path in artifacts.items():
                gcs_path = f"{prefix}/{blob_name}" if prefix else blob_name
                blob = bucket.blob(gcs_path)
                blob.upload_from_filename(local_path)
                uploaded_uris[blob_name] = f"gs://{bucket_name}/{gcs_path}"
                print(f"Uploaded {local_path} to {uploaded_uris[blob_name]}")

            print("\nUpload Complete. Terraform vars:")
            print(f'pickle_object_gcs_uri = "{uploaded_uris["agent.pkl"]}"')
            print(f'requirements_gcs_uri = "{uploaded_uris["requirements.txt"]}"')
            print(f'dependency_files_gcs_uri = "{uploaded_uris["dependencies.tar.gz"]}"')
            
        except Exception as e:
            print(f"Error uploading to GCS: {e}")
            sys.exit(1)
    else:
        print("Skipping upload (no bucket provided). Artifacts check 'build_artifacts_generic/' dir.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package any ADK agent for GCS deployment")
    parser.add_argument("--agent-src-dir", required=True, help="Path to agent source root (containing requirements.txt)")
    parser.add_argument("--import-module", required=True, help="Python import path for the agent (e.g. my_agent.app)")
    parser.add_argument("--agent-var", default="agent", help="Name of the agent variable (default: agent)")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--bucket", help="GCS Bucket Name (optional, if omitted only builds locally)")
    parser.add_argument("--prefix", default="agent-package", help="GCS Object Prefix")
    
    args = parser.parse_args()
    
    package_and_upload(args.agent_src_dir, args.import_module, args.agent_var, args.project, args.bucket, args.prefix)
