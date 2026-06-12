import os
import requests
from google.auth import default
from google.auth.transport.requests import Request
from google.adk.tools.tool_context import ToolContext

class GenericDatastoreClient:
    """
    A generic client to search Gemini Enterprise connected data sources.
    """
    def __init__(self, access_token: str = None):
        """
        Initializes the client. If access_token is not provided,
        it falls back to Application Default Credentials (ADC).
        """
        self.access_token = None
        if access_token: 
            self.access_token = access_token
        else: 
            # Fallback to local user credentials (ADC) for local development
            creds, project_id = default()
            auth_req = Request()
            creds.refresh(auth_req)
            self.access_token = creds.token


    def search(self, query: str, project_id: str, location: str, datastore_id: str) -> dict:
        """
        Performs a search against the Discovery Engine API.
        """
        url = f"https://{location}-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{datastore_id}/servingConfigs/default_search:search"
        
        # If location is global, domain is usually just discoveryengine.googleapis.com
        if location == "global":
            url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{datastore_id}/servingConfigs/default_search:search"


        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "query": f"{query}",
            "pageSize": 10,
            "queryExpansionSpec": {"condition": "AUTO"},
            "spellCorrectionSpec": {"mode": "AUTO"},
            "relevanceScoreSpec": {"returnRelevanceScore": True},
            "languageCode": "en-US",
            "contentSearchSpec": {"snippetSpec": {"returnSnippet": True}},
            "naturalLanguageQueryUnderstandingSpec": {"filterExtractionCondition": "ENABLED"}
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()


def search_emails(query: str, tool_context: ToolContext) -> dict:
    """
    Searches the connected Gemini Enterprise datastore for emails matching the query.
    
    Args:
        query: The search query to find relevant emails.
        
    Returns:
        A dictionary containing the search results, including snippets of matching emails.
    """
    # Retrieve config from environment
    project_id = os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("LOCATION") or os.getenv("GOOGLE_CLOUD_LOCATION")

    datastore_id = os.getenv("DATA_STORE_ID")
    auth_name = os.getenv("AUTH_NAME")

    # Retrieve token from session state
    print(f"Debug: auth_name={auth_name}")
    try:
        state_dict = tool_context.state.to_dict()
        print(f"Debug: Keys in state_dict: {list(state_dict.keys())}")
    except Exception as e:
        print(f"Debug: failed to_dict: {e}")
    access_token = tool_context.state.get(auth_name) if auth_name else None

    client = GenericDatastoreClient(access_token)
    
    # Execute search
    try:
        results = client.search(query, project_id, location, datastore_id)
        return results
    except Exception as e:
        return f"Error searching emails: {e}"

