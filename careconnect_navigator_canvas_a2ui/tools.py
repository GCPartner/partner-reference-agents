import os
import uuid
import logging
from google.adk.tools.tool_context import ToolContext
import ui_renderer

# Set up logging
logging.basicConfig(level=logging.INFO)

# ----------------------------------------------------------------------
# Mock Database (Greater Atlanta Area)
# ----------------------------------------------------------------------
def _generate_providers():
    providers = []
    specialties = ["Dermatology", "Primary Care", "Physical Therapy", "Cardiology", "Pediatrics"]
    zips = ["30303", "30301", "30305", "30022", "30062"]
    
    project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT") or "agentspace-demo-1145-b"
    
    # Generate mock doctors with consistent IDs and profiles
    for zip_code in zips:
        for specialty in specialties:
            base_id = f"{specialty.lower().replace(' ', '_')}_{zip_code}"
            
            providers.append({
                "id": f"{base_id}_1",
                "name": f"Dr. Alice {specialty} (Zip {zip_code})",
                "specialty": specialty,
                "zip": zip_code,
                "networks": ["HMO", "PPO"],
                "photo_url": f"https://storage.googleapis.com/careconnect-nav-canvas-assets-{project_id}/doctor_alice_v2.jpg"
            })
            
            providers.append({
                "id": f"{base_id}_2",
                "name": f"Dr. Bob {specialty} (Zip {zip_code})",
                "specialty": specialty,
                "zip": zip_code,
                "networks": ["PPO"],
                "photo_url": f"https://storage.googleapis.com/careconnect-nav-canvas-assets-{project_id}/doctor_bob_v2.jpg"
            })
            
            providers.append({
                "id": f"{base_id}_3",
                "name": f"Dr. Charles {specialty} (Zip {zip_code}) (Out-of-Network)",
                "specialty": specialty,
                "zip": zip_code,
                "networks": ["OON"],
                "photo_url": f"https://storage.googleapis.com/careconnect-nav-canvas-assets-{project_id}/doctor_charles_v2.jpg"
            })
    return providers

MOCK_PROVIDERS = _generate_providers()

# Mock availability database
MOCK_AVAILABILITY = {
    # Dermatology
    "dermatology_30303_1": ["2025-10-24 09:00", "2025-10-24 10:00", "2025-10-24 14:00"],
    "dermatology_30303_2": ["2025-10-24 11:00", "2025-10-24 15:00"],
    "dermatology_30303_3": ["2025-10-24 13:00"],
    # Physical Therapy
    "physical_therapy_30303_1": ["2025-10-24 10:00", "2025-10-24 11:00"],
}

def _get_provider_by_id(provider_id: str) -> dict:
    for p in MOCK_PROVIDERS:
        if p["id"] == provider_id:
            return p
    # Fallback default profile if not found
    return {
        "id": provider_id,
        "name": "Dr. Unknown CareProvider",
        "specialty": "General Medicine",
        "zip": "30303",
        "networks": ["HMO", "PPO"],
        "photo_url": "https://storage.googleapis.com/careconnect-nav-canvas-assets-agentspace-demo-1145-b/doctor_alice_v2.jpg"
    }


# ----------------------------------------------------------------------
# Wizard Transition Tools
# ----------------------------------------------------------------------

def start_appointment_wizard(plan_type: str = None) -> str:
    """
    Starts or restarts the appointment booking wizard and displays the plan selection UI (Step 1).
    
    Args:
        plan_type: Optional. Pre-selected insurance plan type (HMO or PPO).
        
    Returns:
        The text and A2UI payload for the plan selection screen.
    """
    logging.info(f"[Tool] start_appointment_wizard called with plan_type={plan_type}")
    text_resp = "Welcome to CareConnect appointment wizard! Let's get started. Please select your insurance plan type on the canvas."
    ui_resp = ui_renderer.render_plan_selection(plan_type)
    return f"{text_resp}\n{ui_resp}"


def select_plan_and_continue(plan_type: str) -> str:
    """
    Submits the selected plan type and transitions to the Search Criteria form (Step 2).
    
    Args:
        plan_type: The selected insurance plan type (HMO or PPO).
        
    Returns:
        The search criteria selection UI.
    """
    logging.info(f"[Tool] select_plan_and_continue called with plan_type={plan_type}")
    text_resp = f"Great, you selected the {plan_type} plan. Now let's specify your search criteria on the canvas."
    ui_resp = ui_renderer.render_search_criteria(plan_type)
    return f"{text_resp}\n{ui_resp}"


def select_provider_and_get_availability(provider_id: str, plan_type: str, date: str = "2025-10-24") -> str:
    """
    Selects a provider, queries their availability slots, and renders the slot selection UI (Step 4).
    
    Args:
        provider_id: The selected provider's unique ID.
        plan_type: The active plan type (HMO or PPO).
        date: The date to check (YYYY-MM-DD). Default is '2025-10-24'.
        
    Returns:
        The available slots grid UI.
    """
    logging.info(f"[Tool] select_provider_and_get_availability called for provider={provider_id} on date={date}")
    provider = _get_provider_by_id(provider_id)
    
    slots = MOCK_AVAILABILITY.get(provider_id, ["09:00", "11:00", "14:00"])
    # Ensure they have YYYY-MM-DD prefix
    clean_slots = []
    for s in slots:
        if s.startswith(date):
            clean_slots.append(s.split(" ")[1])
        else:
            clean_slots.append(s)
            
    text_resp = f"Selected {provider['name']}. Please choose an appointment slot on {date} from the options on the canvas."
    ui_resp = ui_renderer.render_availability_grid(clean_slots, provider_id, plan_type, date)
    return f"{text_resp}\n{ui_resp}"


def select_slot_and_continue(provider_id: str, plan_type: str, selected_slot: str) -> str:
    """
    Selects the appointment slot and transitions to the Review & Confirm summary (Step 5).
    
    Args:
        provider_id: The selected provider's ID.
        plan_type: The active plan type (HMO or PPO).
        selected_slot: The chosen date/time slot.
        
    Returns:
        The appointment review summary UI.
    """
    logging.info(f"[Tool] select_slot_and_continue called for provider={provider_id}, slot={selected_slot}")
    provider = _get_provider_by_id(provider_id)
    
    is_oon = plan_type not in provider.get("networks", [])
    network_lbl = "Out-of-Network" if is_oon else "In-Network"
    provider_name = f"{provider['name']} ({network_lbl})"
    
    text_resp = f"Reviewing details: you selected {provider_name} for appointment at {selected_slot}. Please confirm on the canvas."
    ui_resp = ui_renderer.render_review_screen(plan_type, provider_name, provider["photo_url"], selected_slot)
    return f"{text_resp}\n{ui_resp}"


# ----------------------------------------------------------------------
# Standard Data-Query/Action Tools
# ----------------------------------------------------------------------

def search_providers(specialty: str, zip_code: str, plan_type: str) -> str:
    """
    Search for healthcare providers by specialty and zip code, matching network status.
    Transitions to Step 3 (Provider Selection).
    
    Args:
        specialty: The specialty of the doctor (e.g., Dermatology, Physical Therapy).
        zip_code: The 5-digit zip code area to search in (e.g., 30303, 30301).
        plan_type: The user's active insurance plan type (HMO or PPO).
    
    Returns:
        The matched list of provider cards.
    """
    logging.info(f"[Tool] search_providers called with specialty={specialty}, zip={zip_code}, plan={plan_type}")
    
    norm_specialty = specialty.lower().strip()
    # Normalize common synonyms
    if norm_specialty in ["pediatrician", "paediatrician"]:
        norm_specialty = "pediatrics"
    elif norm_specialty in ["gynecologist", "gynaecologist"]:
        norm_specialty = "gynecology"
    elif norm_specialty in ["obstetrician", "child birth", "childbirth"]:
        norm_specialty = "obstetrics"
    elif norm_specialty in ["orthopedic", "bone doctor", "bone case", "bones"]:
        norm_specialty = "orthopedics"
        
    norm_zip = zip_code.strip()
    norm_plan = plan_type.upper().strip()

    filtered_providers = []
    for p in MOCK_PROVIDERS:
        if p["specialty"].lower() == norm_specialty and p["zip"] == norm_zip:
            filtered_providers.append(p)

    text_resp = f"I found {len(filtered_providers)} providers matching {specialty} in {zip_code} for your {plan_type} plan. Please review them on the canvas."
    ui_resp = ui_renderer.render_provider_list(filtered_providers, specialty, zip_code, plan_type)
    return f"{text_resp}\n{ui_resp}"


def book_appointment(provider_id: str, slot: str) -> str:
    """
    Confirms booking an appointment for a provider at a specific time slot (Step 6).
    
    Args:
        provider_id: The unique ID of the provider.
        slot: The specific date and time slot (YYYY-MM-DD HH:MM).
    
    Returns:
        The final booking confirmation UI.
    """
    logging.info(f"[Tool] book_appointment called for provider={provider_id} at slot={slot}")
    provider = _get_provider_by_id(provider_id)
    
    confirmation_id = str(uuid.uuid4())[:8].upper()
    
    text_resp = f"Your appointment has been successfully scheduled with {provider['name']} for {slot}. Confirmation ID: {confirmation_id}."
    ui_resp = ui_renderer.render_confirmation_screen(provider["name"], slot, confirmation_id)
    return f"{text_resp}\n{ui_resp}"
