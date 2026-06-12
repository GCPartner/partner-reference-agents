# Email Digester Agent

The Email Digester agent is an AI assistant built using the Google Agent Development Kit (ADK) that helps users summarize and find information in their emails by integrating with a Gemini Enterprise datastore.

## How it Works

The agent uses a custom tool to search emails stored in a connected Gemini Enterprise datastore. 

### Key Components:
- **`agent.py`**: Defines the `LlmAgent` with instructions to use the search tool.
- **`tools.py`**: Contains the `search_emails` tool which performs the actual search against the Discovery Engine API.

### Data Access and Security:
1. **User-Level Authorization**: The agent retrieves the user's OAuth token from `tool_context.state` (passed by Gemini Enterprise) to ensure that search results respect the user's access permissions (ACLs).
2. **Discovery Engine API**: It calls the `v1alpha` Discovery Engine API to perform federated search across the connected data source (e.g., Google Mail).
3. **Fallback**: For local testing, if the token is not found in the state, it falls back to Application Default Credentials (ADC), though this may not have access to private user datastores.

## Gemini Enterprise Registration

To enable the agent to access the datastore and handle user authorization correctly, it must be registered with Gemini Enterprise using a specific payload structure.

### Critical Configuration:
For Reasoning Engine agents accessing datastores, the Authorization Resource must be specified as an array named `toolAuthorizations` inside `authorizationConfig`, rather than a single string `agentAuthorization`.

Example registration payload snippet:
```json
{
  "displayName": "Email Digester",
  ...
  "authorizationConfig": {
    "toolAuthorizations": [
      "projects/${PROJECT_NUMBER}/locations/global/authorizations/${AUTH_ID}"
    ]
  }
}
```

## How to Apply the Skill to Build Integrations

To build similar integrations for other agents using the `adk_ge_datastore_connector` skill or pattern, follow these steps:

### 1. Implement the Tool in `tools.py`
Use the pattern demonstrated in this agent's `tools.py`:
- Extract the token from `tool_context.state` using the Authorization ID as the key.
- Construct the Discovery Engine API URL using the `v1alpha` endpoint (required for federated search).
- Pass the token in the `Authorization` header.

### 2. Configure Environment Variables
Ensure your agent has access to the following environment variables:
- `PROJECT_ID`: The Google Cloud project ID.
- `LOCATION`: Set to `"global"` for datastores located in the global region (common for Gmail/Drive connectors).
- `DATA_STORE_ID`: The ID of the specific datastore to search.
- `AUTH_NAME`: The ID of the Authorization Resource (used as the key in `tool_context.state`).

### 3. Register with Correct Authorization Structure
When registering the agent with Gemini Enterprise:
- Create an Authorization Resource linked to your OAuth Client.
- Bind it to the agent using the `toolAuthorizations` array inside `authorizationConfig` as shown in the example above.

By following this pattern, you ensure that your agent can securely access enterprise data sources while respecting user permissions.

## References

For more details and a reference implementation of a Gemini Enterprise datastore connector, see the documentation here:
- [ge_datastore_accessor_agent](https://github.com/VeerMuchandi/Learn_ADK_Agents/tree/main/ge_datastore_accessor_agent)
