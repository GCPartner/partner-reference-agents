import os
import sys

# Set dummy environment variables to simulate Reasoning Engine environment
os.environ["PROJECT_ID"] = "partner-engg-agents"
os.environ["GOOGLE_CLOUD_PROJECT"] = "partner-engg-agents"
os.environ["LOCATION"] = "us-central1"
os.environ["GOOGLE_CLOUD_AGENT_ENGINE_ID"] = "test-agent-engine"

print("Importing agent_wrapper...")
try:
    import agent_wrapper
    print("Successfully imported agent_wrapper!")
    print(f"Agent object: {agent_wrapper.agent}")
    
    print("Calling agent.set_up()...")
    if hasattr(agent_wrapper.agent, 'set_up'):
        agent_wrapper.agent.set_up()
        print("Successfully called agent.set_up()!")
    else:
        print("No set_up method found.")
except Exception as e:
    import traceback
    print("Crash occurred during setup/import:")
    traceback.print_exc()
