import argparse
import os
import shutil
import tarfile
import sys

def main():
    parser = argparse.ArgumentParser(description="Package agent for Agent Engine.")
    parser.add_argument("--source", required=True, help="Path to the agent source directory")
    parser.add_argument("--output", default="assets/source.tar.gz", help="Path to the output tar.gz file")
    parser.add_argument("--package-name", help="Name of the python package (default: basename of source)")
    args = parser.parse_args()

    source_path = os.path.abspath(args.source)
    if not os.path.isdir(source_path):
        print(f"Error: Source directory '{source_path}' does not exist.")
        sys.exit(1)

    package_name = args.package_name or os.path.basename(source_path)
    output_path = os.path.abspath(args.output)
    output_dir = os.path.dirname(output_path)
    
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    temp_dir = "temp_package"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        # Create package directory
        pkg_dir = os.path.join(temp_dir, package_name)
        
        # Copy source code
        # Ignore common non-source directories
        shutil.copytree(source_path, pkg_dir, ignore=shutil.ignore_patterns(
            '__pycache__', '*.pyc', '.git', '.venv', '.idea', '.vscode', 'tests', 'test', 'deploy', '.adk'
        ))
        
        # Create app.py wrapper
        app_py_content = f"""from vertexai.agent_engines import AdkApp
from .agent import root_agent
agent = AdkApp(agent=root_agent)
"""
        with open(os.path.join(pkg_dir, "app.py"), "w") as f:
            f.write(app_py_content)
            
        req_path = os.path.join(pkg_dir, "requirements.txt")
        # Read existing requirements
        with open(os.path.join(source_path, "requirements.txt"), "r") as f:
            existing_reqs = f.read()
            
        with open(req_path, "w") as f:
            f.write(existing_reqs)
            f.write("\n# Added for Agent Engine deployment\n")
            f.write("google-cloud-aiplatform[agent_engines,adk]\n")
            
        # Create tar.gz archive
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(pkg_dir, arcname=package_name)
            
        # Generate agent_config.auto.tfvars
        tfvars_path = os.path.join(os.getcwd(), "agent_config.auto.tfvars")
        with open(tfvars_path, "w") as f:
            f.write(f'agent_package_name = "{package_name}"\n')
            
        print(f"Successfully packaged '{package_name}' to '{output_path}'")
        print(f"Generated '{tfvars_path}' with agent_package_name='{package_name}'")
        
    except Exception as e:
        print(f"Error packaging agent: {e}")
        sys.exit(1)
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
