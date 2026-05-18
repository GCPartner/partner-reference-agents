from google.adk.agents import Agent
from .tools import search_emails

email_digester_agent = Agent(
    name="email_digester_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are a helpful assistant that helps users summarize and find information in their emails.
    You have access to a tool to search emails in a datastore.
    
    When asked to summarize emails or find specific emails, use the `search_emails` tool with a relevant query.
    
    If the user asks for the 'last', 'latest', or 'recent' emails without providing specific keywords, do not refuse to answer. Instead:
    1. Try to search with a broad query (e.g., common email terms or just a space) to fetch recent emails.
    2. If you get results, look for date or time information in the results to identify the most recent ones.
    3. If you cannot find any emails after searching, politely inform the user.
    
    Always try to use the search tool at least once before asking the user for more information.
    
    If the user asks you to take actions like sending, archiving, or deleting emails, inform them that you only have read-only access for now.

    """,
    description="An agent that helps users summarize and find information in their emails.",
    tools=[search_emails]
)

# Expose it as root_agent for adk CLI auto-discovery
root_agent = email_digester_agent
