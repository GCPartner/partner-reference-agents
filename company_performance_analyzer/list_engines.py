import os
import vertexai
from vertexai.preview.reasoning_engines import ReasoningEngine

vertexai.init(project="partner-engg-agents", location="us-central1")
try:
    engines = ReasoningEngine.list()
    print(f"Found {len(engines)} reasoning engines:")
    for eng in engines:
        print(f"- ID: {eng.resource_name}")
        print(f"  Display Name: {eng.gca_resource.display_name}")
        print(f"  Create Time: {eng.gca_resource.create_time}")
except Exception as e:
    print(f"Error listing engines: {e}")
