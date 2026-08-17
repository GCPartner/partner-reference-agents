import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from google.adk.tools.tool_context import ToolContext
import base64
import asyncio
def search_plans(data_limit: Optional[str] = None, intl_calling: Optional[bool] = None, provider: Optional[str] = None) -> List[Dict]:
    """
    Search for available phone plans based on user requirements.
    
    Args:
        data_limit: e.g., "high", "unlimited", "5GB".
        intl_calling: True if the user needs international calling.
        provider: e.g., "AT&T", "T-Mobile".
        
    Returns:
        List of matching plans (dicts).
    """
    # Mock Database
    all_plans = [
        {"id": "p1", "name": "Basic Saver", "provider": "T-Mobile", "data": "5GB", "intl_calling": False, "price": 30.00},
        {"id": "p2", "name": "Standard Unlimited", "provider": "Verizon", "data": "Unlimited", "intl_calling": False, "price": 50.00},
        {"id": "p3", "name": "Global Traveler", "provider": "AT&T", "data": "Unlimited", "intl_calling": True, "price": 75.00},
        {"id": "p4", "name": "Data Plus", "provider": "Verizon", "data": "15GB", "intl_calling": False, "price": 45.00},
        {"id": "p5", "name": "Value 10GB", "provider": "T-Mobile", "data": "10GB", "intl_calling": False, "price": 35.00},
        {"id": "p6", "name": "Premium International", "provider": "Verizon", "data": "Unlimited", "intl_calling": True, "price": 85.00},
        {"id": "p7", "name": "Starter 5GB", "provider": "AT&T", "data": "5GB", "intl_calling": False, "price": 25.00},
        {"id": "p8", "name": "Unlimited Starter", "provider": "T-Mobile", "data": "Unlimited", "intl_calling": False, "price": 40.00},
    ]

    results = []
    for plan in all_plans:
        if intl_calling is not None and plan["intl_calling"] != intl_calling:
            continue
        if provider and provider.lower() not in plan["provider"].lower():
            continue
        
        # Numeric threshold comparison for data_limit
        if data_limit:
            dl_str = str(data_limit).lower().strip()
            # If user selected a slider value, parse it
            numeric_val = None
            try:
                # Extract number from string if contains "gb" etc.
                numeric_val = float(''.join(c for c in dl_str if c.isdigit() or c == '.'))
            except ValueError:
                pass

            if "unlimited" in dl_str:
                if plan["data"] != "Unlimited":
                    continue
            elif numeric_val is not None:
                # If target is "Unlimited", it matches any high threshold. 
                # Otherwise, parse mock data size:
                plan_data_val = 100.0 if plan["data"] == "Unlimited" else float(''.join(c for c in plan["data"] if c.isdigit()))
                if plan_data_val < numeric_val:
                    continue
            elif plan["data"].lower() != dl_str:
                continue
            
        results.append(plan)
        
    return results

def search_devices(plan_id: str, model_name: Optional[str] = None, brand: Optional[str] = None) -> List[Dict]:
    """
    Search for mobile devices eligible for the selected plan.
    Higher tier plans unlock more premium devices.

    Args:
        plan_id: The ID or NAME of the plan the user has selected (REQUIRED).
        model_name: specific model to filter by.
        brand: manufacturer to filter by.

    Returns:
        List of available devices for that plan. Note: returns empty if plan_id is invalid.
    """
    # Normalize input to handle LLM sometimes passing the name instead of the ID
    plan_query = plan_id.lower().strip()
    
    # Define Tiers: 1 (Basic), 2 (Mid), 3 (Premium)
    plan_tiers = {
        "p1": 1, "basic saver": 1,
        "p4": 2, "data plus": 2,
        "p2": 3, "standard unlimited": 3,
        "p3": 3, "global traveler": 3,
        "p5": 2, "value 10gb": 2,
        "p6": 3, "premium international": 3,
        "p7": 1, "starter 5gb": 1,
        "p8": 3, "unlimited starter": 3
    }
    
    current_tier = plan_tiers.get(plan_query)
    
    # Fuzzy match fallback
    if not current_tier:
        for key, tier in plan_tiers.items():
            if key in plan_query:
                current_tier = tier
                break

    if not current_tier:
        return [{"error": f"Invalid or missing plan_id: {plan_id}. User must select a valid plan first."}]

    # Mock Database with Minimum Tiers
    all_devices = [
        {"id": "d1", "name": "Google Pixel 9", "brand": "Google", "storage": "128GB", "price": 799.00, "min_tier": 2},
        {"id": "d2", "name": "Google Pixel 9 Pro", "brand": "Google", "storage": "256GB", "price": 999.00, "min_tier": 3},
        {"id": "d3", "name": "Apple iPhone 15", "brand": "Apple", "storage": "128GB", "price": 799.00, "min_tier": 2},
        {"id": "d4", "name": "Apple iPhone 14", "brand": "Apple", "storage": "128GB", "price": 699.00, "min_tier": 1},
        {"id": "d5", "name": "Samsung Galaxy S24", "brand": "Samsung", "storage": "256GB", "price": 850.00, "min_tier": 3},
        {"id": "d6", "name": "Samsung Galaxy A54", "brand": "Samsung", "storage": "128GB", "price": 450.00, "min_tier": 1},
        {"id": "d7", "name": "Google Pixel 8a", "brand": "Google", "storage": "128GB", "price": 499.00, "min_tier": 1},
        {"id": "d8", "name": "Apple iPhone 15 Pro", "brand": "Apple", "storage": "256GB", "price": 999.00, "min_tier": 3},
    ]

    results = []
    for device in all_devices:
        # Check plan tier eligibility
        if current_tier < device["min_tier"]:
            continue
            
        if brand and brand.lower() not in device["brand"].lower():
            continue
        if model_name and model_name.lower() not in device["name"].lower():
            continue
        
        # Remove min_tier from output so as not to confuse the LLM
        clean_device = {k: v for k, v in device.items() if k != "min_tier"}
        results.append(clean_device)
    
    return results

def calculate_total(plan_price: float, device_price: float = 0.0, discount_percent: float = 0.0) -> Dict:
    """
    Calculate the total monthly and upfront cost.

    Args:
        plan_price: Monthly cost of the plan.
        device_price: Upfront cost of the device.
        discount_percent: Any discount to apply (0-100).

    Returns:
        Dict with subtotal, discount_amount, and final_total.
    """
    total = plan_price + device_price
    discount_amount = total * (discount_percent / 100)
    final_total = total - discount_amount
    
    return {
        "monthly_plan_cost_after_discount": round(plan_price * (1 - discount_percent/100), 2),
        "upfront_device_cost_after_discount": round(device_price * (1 - discount_percent/100), 2),
        "total_first_month": round(final_total, 2)
    }

def request_manager_discount(justification: str) -> Dict:
    """
    Request a discretionary discount from a virtual manager.
    
    Args:
        justification: Reason why the customer deserves a discount.
        
    Returns:
        Dict indicating if approved and the discount percentage (e.g. 10 or 15).
    """
    # Simulate manager logic: usually approves 10%, sometimes 15% if justified
    if len(justification) > 10:
        return {"approved": True, "discount_percent": 15.0, "message": "Manager approved 15% discount."}
    return {"approved": True, "discount_percent": 10.0, "message": "Manager approved 10% discount."}

def create_order(plan_id: str, device_id: Optional[str] = None, applied_discount: float = 0.0) -> Dict:
    """
    Finalize the purchase.

    Args:
        plan_id: Selected plan ID (REQUIRED).
        device_id: Selected device ID (optional).
        applied_discount: The discount percentage applied.

    Returns:
        Order confirmation details. Note: If plan_id is missing this will return a failure.
    """
    if not plan_id:
        return {"status": "FAILED", "reason": "A valid plan_id is required to create an order."}

    order_id = f"ORD-{random.randint(1000, 9999)}"
    delivery = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    
    return {
        "status": "SUCCESS",
        "order_id": order_id,
        "expected_delivery": delivery,
        "message": "Order processed successfully."
    }


