import json
import logging
from pathlib import Path
from google.adk.tools import ToolContext

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Basic file read/write locations
DATA_DIR = Path(__file__).parent / "data"

def read_strategic_plan(tool_context: ToolContext) -> dict:
    """Read the agency's static strategic plan to verify alignment of project proposals.
    
    This text file contains the high-level goals and priorities of the agency. 
    It must be consulted to ensure a proposed project fits within the current organizational mission.
    """
    plan_path = DATA_DIR / "strategic_plan.txt"
    try:
        with open(plan_path, "r") as f:
            plan_content = f.read()
        return {"status": "success", "data": plan_content}
    except Exception as e:
        logger.error(f"Error reading strategic plan: {e}")
        return {"status": "error", "message": str(e)}

def search_grants_gov(keywords: list[str], tool_context: ToolContext) -> dict:
    """Search the Grants.gov database for funding opportunities matching the given keywords.
    

    Args:
        keywords: A list of specific search terms derived from the project proposal.
        
    Returns:
        A dictionary containing a list of top matching grant opportunities, including their IDs, titles, descriptions, and eligibility requirements.
    """
    logger.info(f"Mocking Grants.gov search for keywords: {keywords}")
    # Mock response
    mock_results = [
        {
            "grant_id": "GG-2026-AI-01",
            "title": "Public Health AI Innovation Grant",
            "agency": "NIH",
            "max_funding": 5000000,
            "description": "Funding for projects utilizing artificial intelligence to improve scalable public health infrastructure.",
            "eligibility": "Local government agencies, research institutions."
        },
        {
            "grant_id": "GG-2026-CYBER-02",
            "title": "Municipal Cyber Resilience Fund",
            "agency": "CISA",
            "max_funding": 2500000,
            "description": "Support for local governments to upgrade data center security and cyber defense capabilities.",
            "eligibility": "State and local government entities."
        }
    ]
    return {
        "status": "success", 
        "data": mock_results
    }

def fetch_sap_financial_data(project_budget_requirement: int, tool_context: ToolContext) -> dict:
    """Fetch necessary historical financial records and audited statements from the SAP system to support the grant application.
    

    Args:
        project_budget_requirement: The total amount of funding being requested, used to pull relevant scale financial documents.
    """
    logger.info(f"Mocking SAP data retrieval for budget scale: {project_budget_requirement}")
    # Mock data
    return {
        "status": "success", 
        "data": {
            "last_audit_date": "2025-01-15",
            "audit_status": "Unqualified Opinion (Clean)",
            "annual_operating_budget": 150000000,
            "financial_contact": "Jane Doe, CFO",
            "system_generated_budget_narrative": f"The agency maintains a strong financial position capable of managing the requested ${project_budget_requirement}."
        }
    }

def fetch_workday_hr_data(project_domain: str, tool_context: ToolContext) -> dict:
    """Fetch personnel profiles, historical KPIs, and program management data from Workday relevant to the project domain.
    

    Args:
        project_domain: The general field of the project (e.g., 'Public Health', 'Cybersecurity') to identify key personnel.
    """
    logger.info(f"Mocking Workday HR/KPI data retrieval for domain: {project_domain}")
    # Mock data based on domain
    kpis = "Maintained 99.9% uptime across all systems; successfully delivered 5 major public infrastructure projects in 2024-2025."
    if "health" in project_domain.lower() or "ai" in project_domain.lower():
         kpis = "Processed 1M+ health records with 99.99% accuracy; led cross-functional team of 50 data scientists."
         
    return {
        "status": "success",
        "data": {
            "key_personnel_available": 3,
            "lead_manager": "Dr. Smith",
            "relevant_historical_kpis": kpis,
            "diversity_metrics": "Exceeds federal guidelines for inclusivity and equal opportunity employment."
        }
    }

def generate_submission_package(draft_text: str, target_grant_id: str, tool_context: ToolContext) -> dict:
    """Compile the finalized grant application draft and all supporting documentation into a formal submission package.
    

    Args:
        draft_text: The complete textual draft of the grant application.
        target_grant_id: The ID of the grant being applied for.
    """
    logger.info(f"Mocking compilation of submission package for grant {target_grant_id}")
    
    # In a real implementation this might generate a PDF or Word doc. Here we just mock it.
    package_summary = {
        "submission_id": f"SUB-{target_grant_id}-999",
        "word_count": len(draft_text.split()),
        "attachments_included": ["Audited Financials (SAP)", "Key Personnel Resumes (Workday)", "Strategic Alignment Memo"],
        "readiness": "Ready for Executive Review"
    }
    
    return {"status": "success", "package_summary": package_summary, "compiled_draft_preview": draft_text[:200] + "..."}

def save_intake_details(project_summary: str, search_keywords: list[str], budget_required: int, project_domain: str, tool_context: ToolContext) -> dict:
    """Save the extracted project details to the shared state for downstream agents.
    

    Args:
        project_summary: Concise summary of the project.
        search_keywords: List of keywords for Grants.gov.
        budget_required: Estimated budget needed (integer).
        project_domain: General field (e.g., 'Public Health').
    """
    tool_context.state["project_summary"] = project_summary
    tool_context.state["search_keywords"] = search_keywords
    tool_context.state["budget_required"] = budget_required
    tool_context.state["project_domain"] = project_domain
    tool_context.state["force_end"] = True
    return {"status": "success", "message": "Intake details saved to state."}

def save_selected_grant(target_grant_id: str, title: str, description: str, tool_context: ToolContext) -> dict:
    """Save the selected grant details to the shared state.
    

    Your turn ends immediately after calling this tool. DO NOT output any conversational text. 

    Args:
        target_grant_id: ID of the selected grant.
        title: Title of the grant.
        description: Description of the grant.
    """
    tool_context.state["selected_grant"] = target_grant_id
    tool_context.state["selected_grant_title"] = title
    tool_context.state["selected_grant_description"] = description
    return {"status": "success", "message": "Selected grant saved to state."}

def save_application_draft(draft_text: str, tool_context: ToolContext) -> dict:
    """Save the finalized application draft to the shared state.
    

    Your turn ends immediately after calling this tool. DO NOT output any conversational text. 

    Args:
        draft_text: The string text of the drafted application.
    """
    tool_context.state["application_draft"] = draft_text
    return {"status": "success", "message": "Application draft saved to state."}
