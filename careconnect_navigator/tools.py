from google.adk.tools.tool_context import ToolContext
import logging

# Set up logging to verify tool calls
logging.basicConfig(level=logging.INFO)

# ----------------------------------------------------------------------
# Mock Database (Greater Atlanta Area)
# ----------------------------------------------------------------------
# Programmatic Data Generator to ensure 3 per specialty/zip coverage
def _generate_providers():
    providers = []
    specialties = ["Dermatology", "Primary Care", "Physical Therapy", "Cardiology", "Pediatrics", "Family Medicine", "Orthopedics", "Oncology", "Gynecology", "Obstetrics"]
    zips = ["30303", "30301", "30305", "30022", "30062"]
    
    # We generate 3 doctors per specialty per zip with distinct network profiles
    for zip_code in zips:
        for specialty in specialties:
            base_id = f"{specialty.lower().replace(' ', '_')}_{zip_code}"
            
            # Provider 1: HMO + PPO (Dual Network)
            providers.append({
                "id": f"{base_id}_1",
                "name": f"Dr. Alice {specialty} (Zip {zip_code})",
                "specialty": specialty,
                "zip": zip_code,
                "networks": ["HMO", "PPO"]
            })
            
            # Provider 2: PPO Only
            providers.append({
                "id": f"{base_id}_2",
                "name": f"Dr. Bob {specialty} (Zip {zip_code})",
                "specialty": specialty,
                "zip": zip_code,
                "networks": ["PPO"]
            })
            
            # Provider 3: Out-of-Network Only
            providers.append({
                "id": f"{base_id}_3",
                "name": f"Dr. Charles {specialty} (Zip {zip_code}) (Out-of-Network)",
                "specialty": specialty,
                "zip": zip_code,
                "networks": ["OON"]
            })
    return providers

MOCK_PROVIDERS = _generate_providers()


MOCK_AVAILABILITY = {
    "derma_1": ["2025-10-24 09:00", "2025-10-24 10:00", "2025-10-24 14:00"],
    "derma_2": ["2025-10-24 11:00", "2025-10-24 15:00"],
    "derma_3": ["2025-10-24 13:00"],
    "pcp_1": ["2025-10-24 08:00", "2025-10-24 09:00"],
    "pt_1": ["2025-10-24 10:00", "2025-10-24 11:00"],
}

# ----------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------

def search_providers(specialty: str, zip_code: str, plan_type: str, date_time: str = None) -> dict:
    """
    Search for healthcare providers by specialty, zip code, and network status.
    Optionally filters by availability if date_time is provided.
    
    Args:
        specialty: The specialty of the doctor (e.g., Dermatology, Primary Care).
        zip_code: The 5-digit zip code area to search in (e.g., 30303, 30301).
        plan_type: The user's insurance plan type (HMO or PPO).
        date_time: Optional. The date/time to check availability (e.g., 2024-10-24, 2024-10-24 09:00).
    
    Returns:
        A list of matching providers with their network status (In-Network or out-of-network).
    """
    logging.info(f"[Tool] search_providers called with specialty={specialty}, zip={zip_code}, plan={plan_type}, date_time={date_time}")
    
    filtered_providers = []
    
    # Normalize inputs and handle common synonyms
    norm_specialty = specialty.lower().strip()
    
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


    if norm_plan not in ["HMO", "PPO"]:
        return {"status": "error", "message": "Invalid plan type. Must be HMO or PPO."}

    for p in MOCK_PROVIDERS:
        if p["specialty"].lower() == norm_specialty and p["zip"] == norm_zip:
            # Determine network status
            is_in_network = norm_plan in p["networks"]
            network_label = "In-Network" if is_in_network else "Out-of-Network"
            
            # Simulate availability check if date_time provided
            if date_time:
                # Simple mock: skip if id ends with _3 (just to show tool filtering works)
                if p["id"].endswith("_3"):
                    continue
            
            filtered_providers.append({
                "id": p["id"],
                "name": p["name"],
                "specialty": p["specialty"],
                "zip": p["zip"],
                "network_status": network_label
            })

    return {"status": "success", "results": filtered_providers}


def check_availability(provider_id: str, date: str, tool_context: ToolContext) -> dict:
    """
    Retrieve available time slots for a specific provider on a given date.
    
    Args:
        provider_id: The unique ID of the provider.
        date: The date to check availability for (YYYY-MM-DD).
    
    Returns:
        A list of available time slots or an error if not found.
    """
    logging.info(f"[Tool] check_availability called for provider={provider_id} on date={date}")
    
    if provider_id not in MOCK_AVAILABILITY:
        # If no explicit mock availability exists, generate some dummy slots
        # Just to make the demo work for all providers
        return {
            "status": "success",
            "provider_id": provider_id,
            "date": date,
            "slots": [f"{date} 09:00", f"{date} 10:00", f"{date} 14:00"]
        }

    slots = MOCK_AVAILABILITY.get(provider_id, [])
    # Filter by date if slots contain date
    filtered_slots = [s for s in slots if s.startswith(date)]

    return {
        "status": "success",
        "provider_id": provider_id,
        "date": date,
        "slots": filtered_slots
    }


def book_appointment(provider_id: str, slot: str, tool_context: ToolContext) -> dict:
    """
    Confirm booking an appointment for a provider at a specific time slot.
    
    Args:
        provider_id: The unique ID of the provider.
        slot: The specific date and time slot (YYYY-MM-DD HH:MM).
    
    Returns:
        Confirmation details or error if slot is unavailable.
    """
    logging.info(f"[Tool] book_appointment called for provider={provider_id} at slot={slot}")
    
    # In a real system, we would check if the slot is still open in DB
    # For mock, we just confirm it.
    
    import uuid
    confirmation_id = str(uuid.uuid4())[:8]
    
    return {
        "status": "success",
        "message": f"Appointment successfully booked for provider {provider_id} at {slot}.",
        "confirmation_id": confirmation_id,
        "provider_id": provider_id,
        "slot": slot
    }
