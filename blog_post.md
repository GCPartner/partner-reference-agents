# Deploying ADK Agents on Google Agent Runtime: A Complete A2A Guide

You've built a powerful AI agent using the Google Agent Development Kit (ADK). It works brilliantly on your local machine, handling queries and calling tools with ease. But now comes the real challenge: **How do you take that agent and make it communicate seamlessly with other agents or custom clients in a production environment?**

Today, we are diving into how to solve this by deploying your ADK agent as an **A2A (Agent-to-Agent)** agent on the **Google Agent Runtime** (formerly Vertex AI Agent Engine).

If you want to build agents that can speak a standardized protocol for message routing and session management, this guide is for you. We will focus on a pure A2A deployment, perfect for agents that handle text and structured data.

## Why A2A on Google Agent Runtime?

Google Agent Runtime provides a powerful, serverless environment to host your AI agents. By using the A2A protocol, you ensure that your agent speaks a standard language for message routing, session management, and task tracking. This makes it easier to integrate your agent into larger systems or connect it to custom frontends like Gemini Enterprise.

Here is how you can take a standard ADK agent and make it A2A-ready in three simple steps.

---

## Step 1: Create a Custom Agent Executor

The heart of an A2A deployment is the custom `AgentExecutor`. By default, ADK agents run in a local loop. To bridge them to the A2A protocol on Agent Runtime, we override the execution loop to yield standard A2A message parts.

Create an `agent_executor.py` file in your agent directory. This file will inherit from `agent_execution.AgentExecutor` and wrap your ADK agent's async run stream.

Here is a simple template:

```python
import logging
from a2a import types
from a2a import utils
from a2a.server import agent_execution
from a2a.server import events
from a2a.server import tasks
import agent # Your ADK agent
from google.adk import runners
from google.genai import types as genai_types

class AdkAgentToA2AExecutor(agent_execution.AgentExecutor):
    def __init__(self):
        self._agent = agent.root_agent
        self._runner = runners.Runner(app_name=self._agent.name, agent=self._agent)
        self._user_id = "remote_agent"

    async def execute(self, context: agent_execution.RequestContext, event_queue: events.EventQueue) -> None:
        query = context.get_user_input()
        
        # Create a task if not exists
        task = context.current_task or utils.new_task(context.message)
        if not context.current_task:
            await event_queue.enqueue_event(task)
            
        updater = tasks.TaskUpdater(event_queue, task.id, task.context_id)
        await updater.start_work()

        # Run the ADK agent
        final_response_content = ""
        content = genai_types.Content(role="user", parts=[{"text": query}])
        
        async for event in self._runner.run_async(user_id=self._user_id, session_id=task.context_id, new_message=content):
            if event.is_final_response():
                final_response_content += event.content.parts[0].text

        # Yield the text response as a standard A2A TextPart
        parts = [types.Part(root=types.TextPart(text=final_response_content))]
        await updater.add_artifact(parts, name="response")
        await updater.complete()
```

---

## Step 2: Deploying with the Python SDK

Next, we use the Vertex AI Python SDK to package and deploy the agent. We use the `A2aAgent` template provided by the SDK and pass our custom executor builder.

Create a `deploy_ae.py` script:

```python
import os
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from a2a.types import AgentSkill
from google.genai import types

import agent_executor

def deploy():
    vertexai.init(project="your-project-id", location="us-central1", staging_bucket="gs://your-bucket")

    # Define Agent Card
    agent_skill = AgentSkill(id="my_skill", name="My Skill", description="Does something helpful")
    agent_card = create_agent_card(agent_name="My Agent", description="My Agent", skills=[agent_skill])
    
    # Instantiate A2aAgent
    a2a_agent = A2aAgent(agent_card=agent_card, agent_executor_builder=agent_executor.AdkAgentToA2AExecutor)

    # Deploy
    client = vertexai.Client(project="your-project-id", location="us-central1", http_options=types.HttpOptions(api_version="v1beta1"))
    
    config = {
        "requirements": ["google-adk==1.28.1", "a2a-sdk==0.3.22"], # Pin your versions!
        "extra_packages": ["agent_executor.py", "agent.py", "tools.py"]
    }
    
    remote_agent = client.agent_engines.create(agent=a2a_agent, config=config)
    print(f"Agent created: {remote_agent.name}")

if __name__ == "__main__":
    deploy()
```

**Crucial Tip**: Always pin your dependency versions in the `requirements` list to match your local environment. This prevents unpickling errors in the remote container!

---

## Step 3: Test the A2A Agent

Once deployed, you can test your agent by interacting with its HTTP endpoints. 

### 1. Fetch the Agent Card
Before sending messages, it is a good practice to fetch the **Agent Card** to verify that the endpoint is active. You can do this by sending a GET request to the card endpoint:

```text
GET https://[LOCATION]-aiplatform.googleapis.com/v1beta1/projects/[PROJECT_ID]/locations/[LOCATION]/reasoningEngines/[ENGINE_ID]/a2a/v1/card
```

This will return a JSON object describing the agent's identity and skills.

### 2. Send a Message
To send a message, use a POST request to the `message:send` endpoint. One thing to keep in mind is that the payload must match the exact **Protobuf schema** expected by the A2A server, which sometimes differs from the Pydantic models in the SDK.

Here is the working payload structure for sending a message:

```json
{
  "request": {
    "message_id": "unique-msg-id",
    "role": "ROLE_USER",
    "content": [
      {
        "text": "Your message here"
      }
    ]
  },
  "configuration": {
    "blocking": true
  }
}
```

- Use `request` instead of `message` at the top level.
- Use `content` instead of `parts` inside the message object.
- Use `ROLE_USER` as the role string.
- Set `blocking: true` in configuration to wait for the agent's response synchronously.

## Conclusion

Deploying ADK agents as A2A agents on Google Agent Runtime opens up great possibilities for interoperability and scale. By following this guide, you can ensure your agents are ready for the future of agentic ecosystems.

Happy coding!
