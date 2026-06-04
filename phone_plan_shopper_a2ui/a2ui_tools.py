import json
import os
import jsonschema
from typing import List, Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext

from vertexai.preview.generative_models import Part
import tools # Import original tools

def get_device_image_url(device_name: str) -> str:
    name_lower = device_name.lower()
    if "pixel 9" in name_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Google_Pixel_9_%28Obsidian%29_front.svg/500px-Google_Pixel_9_%28Obsidian%29_front.svg.png"
    elif "iphone 15" in name_lower or "iphone 14" in name_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Front_of_iPhone_15_Pro_Max.jpg/500px-Front_of_iPhone_15_Pro_Max.jpg"
    elif "s24" in name_lower or "a54" in name_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Samsung-Galaxy-S24-Ultra-Front.jpg/960px-Samsung-Galaxy-S24-Ultra-Front.jpg"
    elif "pixel 8a" in name_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Google_Pixel_8_Rose_front.jpg/500px-Google_Pixel_8_Rose_front.jpg"
    return "https://placehold.co/100x100"

def show_discount_request_ui() -> str:
    components = [
        { "id": "discount_card", "component": { "Card": { "child": "discount_col" } } },
        { "id": "discount_col", "component": { "Column": { "children": { "explicitList": ["discount_txt", "discount_btns"] } } } },
        { "id": "discount_txt", "component": { "Text": { "text": { "literalString": "Would you like me to request a manager discount for you?" }, "usageHint": "h4" } } },
        { "id": "discount_btns", "component": { "Row": { "children": { "explicitList": ["yes_btn", "no_btn"] }, "gap": "10px" } } },
        { "id": "yes_btn", "component": { "Button": { "child": "yes_txt", "primary": True, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Yes, please request a discount."}}] } } } },
        { "id": "yes_txt", "component": { "Text": { "text": { "literalString": "Yes" } } } },
        { "id": "no_btn", "component": { "Button": { "child": "no_txt", "primary": False, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "No, thanks."}}] } } } },
        { "id": "no_txt", "component": { "Text": { "text": { "literalString": "No" } } } },
    ]
    
    payload = {
        "a2ui_messages": [
            { "beginRendering": { "surfaceId": "discount_request", "root": "discount_card" } },
            { "surfaceUpdate": { "surfaceId": "discount_request", "components": components } }
        ]
    }
    
    return f"Would you like me to request a manager discount for you?\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def render_ui(a2ui_json: str, tool_context: ToolContext = None):
    """Submits the A2UI JSON payload to the client screen to dynamically render user interfaces like forms, cards, and lists.
    
    CRITICAL INSTRUCTIONS FOR LLM:
    - You MUST call this tool INSTEAD of printing raw JSON codeblocks into the chat stream.
    - Pass the entire A2UI JSON payload as a string to the `a2ui_json` parameter.
    - The JSON payload must exactly adhere to the official A2UI Schema v0.8.
    - If you receive a JSON validation error back from this tool, YOU MUST fix your schema based on the error and call the tool again!
    - Example form components: Slider, CheckBox, TextField, Button. DO NOT make up component names.
    
    Args:
        a2ui_json: A valid JSON string containing the A2UI messages array.
            Format: '[{"beginRendering": {"surfaceId": "main", "root": "x"}}, {"surfaceUpdate": {"surfaceId": "main", "components": [...]}}]'
    Returns:
        A binary Part object containing the UI payload for native rendering.
    """
    schema_path = os.path.join(os.path.dirname(__file__), 'a2ui_schema.json')
    try:
        a2ui_messages = json.loads(a2ui_json)
        with open(schema_path, 'r') as f:
            a2ui_schema = json.load(f)
            
        for i, msg in enumerate(a2ui_messages):
            jsonschema.validate(instance=msg, schema=a2ui_schema)
            
        # Return as binary Part
        # Option D: Native Vertex AI Part
        return Part.from_data(data=a2ui_json.encode('utf-8'), mime_type="application/json+a2ui")
        
    except json.JSONDecodeError as e:
        return f"CRITICAL SYNTAX ERROR in your JSON string:\nError: {e.msg}\nLocation: line {e.lineno}, col {e.colno}\nRemedy: Check for extra/missing braces, commas, or quotes near the error location, fix the JSON, and call `render_ui` again!"

    except jsonschema.exceptions.ValidationError as e:
        # Give LLM a path to debug the hallucination.
        path_str = ' -> '.join(str(p) for p in e.path) if e.path else 'Root Level'
        return f"CRITICAL VALIDATION ERROR in your a2ui_messages at message index {i}:\nError: {e.message}\nPath: {path_str}\nRemedy: The component you specified might not match the schema (e.g., using 'RadioGroup' instead of supported schema types, or missing required fields). Read the error carefully, fix the JSON structure, and call `render_ui` again!"
        
    except Exception as e:
        return f"System Error processing A2UI payload: {str(e)}"

def show_plans_ui(plans: List[Dict[str, Any]]) -> str:
    """Generates A2UI JSON for a list of plans and returns it as a string with the delimiter.
    
    Args:
        plans: List of plan dictionaries.
    """
    print(f"Calling show_plans_ui with {len(plans)} plans")
    components = [
        { "id": "plan_select_card", "component": { "Card": { "child": "plan_select_col" } } },
        { "id": "plan_select_col", "component": { "Column": { "children": { "explicitList": ["plan_title", "plan_list_col"] } } } },
        { "id": "plan_title", "component": { "Text": { "text": { "literalString": "Please select a plan:" }, "usageHint": "h3" } } },
    ]
    
    plan_item_ids = []
    for i, plan in enumerate(plans):
        item_id = f"plan_item_{i}"
        row_id = f"plan_row_{i}"
        logo_id = f"plan_logo_{i}"
        details_id = f"plan_details_{i}"
        name_id = f"plan_name_{i}"
        price_id = f"plan_price_{i}"
        btn_id = f"select_btn_{i}"
        txt_id = f"select_txt_{i}"
        
        plan_item_ids.append(item_id)
        
        logo_url = "https://placehold.co/100x100"
        if "at&t" in plan.get("provider", "").lower():
            logo_url = "https://upload.wikimedia.org/wikipedia/commons/5/5c/AT%26T-logo_2016.png"
        elif "verizon" in plan.get("provider", "").lower():
             logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Verizon_2024.svg/1280px-Verizon_2024.svg.png"
        elif "t-mobile" in plan.get("provider", "").lower():
             logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/T-Mobile_US_Logo_2022_RGB_Magenta_on_Transparent.svg/1280px-T-Mobile_US_Logo_2022_RGB_Magenta_on_Transparent.svg.png"
             
        components.extend([
            { "id": item_id, "component": { "Card": { "child": row_id } } },
            { "id": row_id, "component": { "Row": { "children": { "explicitList": [logo_id, details_id, btn_id] }, "alignment": "center", "distribution": "spaceBetween" } } },
            { "id": logo_id, "weight": 1, "component": { "Image": { "url": { "literalString": logo_url }, "fit": "contain" } } },
            { "id": details_id, "weight": 3, "component": { "Column": { "children": { "explicitList": [name_id, price_id] } } } },
            { "id": name_id, "component": { "Text": { "text": { "literalString": f"{plan['name']} ({plan['provider']})" }, "usageHint": "body" } } },
            { "id": price_id, "component": { "Text": { "text": { "literalString": f"${plan['price']}/mo" }, "usageHint": "caption" } } },
            { "id": btn_id, "weight": 1, "component": { "Button": { "child": txt_id, "primary": True, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": f"I select the {plan['name']} plan."}}, {"key": "selected_plan_id", "value": {"literalString": plan['id']}}] } } } },
            { "id": txt_id, "component": { "Text": { "text": { "literalString": "Select" } } } }
        ])
        
    components.append({ "id": "plan_list_col", "component": { "Column": { "children": { "explicitList": plan_item_ids } } } })
    
    payload = {
        "a2ui_messages": [
            { "beginRendering": { "surfaceId": "plan_selection", "root": "plan_select_card" } },
            { "surfaceUpdate": { "surfaceId": "plan_selection", "components": components } }
        ]
    }
    
    return f"Here are the plans that match your needs:\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def show_devices_ui(devices: List[Dict[str, Any]]) -> str:
    """Generates A2UI JSON for a list of devices and returns it as a string with the delimiter.
    
    Args:
        devices: List of device dictionaries.
    """
    print(f"Calling show_devices_ui with {len(devices)} devices")
    components = [
        { "id": "device_select_card", "component": { "Card": { "child": "device_select_col" } } },
        { "id": "device_select_col", "component": { "Column": { "children": { "explicitList": ["device_title", "device_list_col"] } } } },
        { "id": "device_title", "component": { "Text": { "text": { "literalString": "Please select a device:" }, "usageHint": "h3" } } },
    ]
    
    device_item_ids = []
    for i, device in enumerate(devices):
        item_id = f"device_item_{i}"
        row_id = f"device_row_{i}"
        img_id = f"device_img_{i}"
        details_id = f"device_details_{i}"
        name_id = f"device_name_{i}"
        price_id = f"device_price_{i}"
        btn_id = f"select_btn_{i}"
        txt_id = f"select_txt_{i}"
        
        device_item_ids.append(item_id)
        
        img_url = get_device_image_url(device.get("name", ""))
            
        components.extend([
            { "id": item_id, "component": { "Card": { "child": row_id } } },
            { "id": row_id, "component": { "Row": { "children": { "explicitList": [img_id, details_id, btn_id] }, "alignment": "center", "distribution": "spaceBetween" } } },
            { "id": img_id, "weight": 1, "component": { "Image": { "url": { "literalString": img_url }, "fit": "contain" } } },
            { "id": details_id, "weight": 3, "component": { "Column": { "children": { "explicitList": [name_id, price_id] } } } },
            { "id": name_id, "component": { "Text": { "text": { "literalString": f"{device['name']} ({device['brand']})" }, "usageHint": "body" } } },
            { "id": price_id, "component": { "Text": { "text": { "literalString": f"${device['price']}" }, "usageHint": "caption" } } },
            { "id": btn_id, "weight": 1, "component": { "Button": { "child": txt_id, "primary": True, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": f"I select the {device['name']}."}}, {"key": "selected_device_id", "value": {"literalString": device['id']}}] } } } },
            { "id": txt_id, "component": { "Text": { "text": { "literalString": "Select" } } } }
        ])
        
    components.append({ "id": "device_list_col", "component": { "Column": { "children": { "explicitList": device_item_ids } } } })
    
    payload = {
        "a2ui_messages": [
            { "beginRendering": { "surfaceId": "device_selection", "root": "device_select_card" } },
            { "surfaceUpdate": { "surfaceId": "device_selection", "components": components } }
        ]
    }
    
    return f"Here are the devices compatible with your selected plan:\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def search_plans_and_show_ui(data_limit: Optional[str] = None, intl_calling: Optional[bool] = None, provider: Optional[str] = None) -> str:
    """Searches for plans and returns the A2UI JSON for the results.
    
    Use this tool when the user asks to search for or show plans. It guarantees correct UI rendering with images.
    """
    plans = tools.search_plans(data_limit, intl_calling, provider)
    return show_plans_ui(plans)

def search_devices_and_show_ui(plan_id: str, model_name: Optional[str] = None, brand: Optional[str] = None) -> str:
    """Searches for devices and returns the A2UI JSON for the results.
    
    Use this tool when the user asks to search for or show devices. It guarantees correct UI rendering with images.
    """
    devices = tools.search_devices(plan_id, model_name, brand)
    return show_devices_ui(devices)

def show_order_summary_ui(plan_id: str, device_id: Optional[str] = None, discount_percent: float = 0.0) -> str:
    """Generates A2UI JSON for the order summary (cart) and returns it as a string with the delimiter.
    
    Use this tool when the user is ready to review their order before placing it.
    """
    all_plans = tools.search_plans()
    selected_plan = next((p for p in all_plans if p["id"] == plan_id), None)
    
    plan_logo_url = "https://placehold.co/100x100"
    if selected_plan:
        provider = selected_plan.get("provider", "").lower()
        if "at&t" in provider:
            plan_logo_url = "https://upload.wikimedia.org/wikipedia/commons/5/5c/AT%26T-logo_2016.png"
        elif "verizon" in provider:
            plan_logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Verizon_2024.svg/1280px-Verizon_2024.svg.png"
        elif "t-mobile" in provider:
            plan_logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/T-Mobile_US_Logo_2022_RGB_Magenta_on_Transparent.svg/1280px-T-Mobile_US_Logo_2022_RGB_Magenta_on_Transparent.svg.png"

    selected_device = None
    device_img_url = None
    if device_id:
        all_devices = tools.search_devices(plan_id)
        selected_device = next((d for d in all_devices if d["id"] == device_id), None)
        if selected_device:
            device_img_url = get_device_image_url(selected_device.get("name", ""))

    plan_price = selected_plan["price"] if selected_plan else 0.0
    device_price = selected_device["price"] if selected_device else 0.0
    totals = tools.calculate_total(plan_price, device_price, discount_percent)

    plan_price_str = f"${totals['monthly_plan_cost_after_discount']}/mo"
    if discount_percent > 0:
        plan_price_str = f"${plan_price}/mo -> ${totals['monthly_plan_cost_after_discount']}/mo (Saved {discount_percent}%)"

    device_price_str = f"${totals['upfront_device_cost_after_discount']}"
    if selected_device and discount_percent > 0:
        device_price_str = f"${device_price} -> ${totals['upfront_device_cost_after_discount']} (Saved {discount_percent}%)"

    components = [
        { "id": "summary_card", "component": { "Card": { "child": "summary_col" } } },
        { "id": "summary_col", "component": { "Column": { "children": { "explicitList": ["summary_title", "plan_summary_row"] } } } },
        { "id": "summary_title", "component": { "Text": { "text": { "literalString": "Order Summary" }, "usageHint": "h3" } } },
        
        { "id": "plan_summary_row", "component": { "Row": { "children": { "explicitList": ["plan_logo", "plan_txt_col"] }, "alignment": "center" } } },
        { "id": "plan_logo", "weight": 1, "component": { "Image": { "url": { "literalString": plan_logo_url }, "fit": "contain" } } },
        { "id": "plan_txt_col", "weight": 3, "component": { "Column": { "children": { "explicitList": ["plan_name_txt", "plan_price_txt"] } } } },
        { "id": "plan_name_txt", "component": { "Text": { "text": { "literalString": f"Plan: {selected_plan['name']}" if selected_plan else "Unknown Plan" } } } },
        { "id": "plan_price_txt", "component": { "Text": { "text": { "literalString": plan_price_str } } } },
    ]
    
    summary_children = ["summary_title", "plan_summary_row"]
    
    if selected_device:
        components.extend([
            { "id": "device_summary_row", "component": { "Row": { "children": { "explicitList": ["device_img", "device_txt_col"] }, "alignment": "center" } } },
            { "id": "device_img", "weight": 1, "component": { "Image": { "url": { "literalString": device_img_url }, "fit": "contain" } } },
            { "id": "device_txt_col", "weight": 3, "component": { "Column": { "children": { "explicitList": ["device_name_txt", "device_price_txt"] } } } },
            { "id": "device_name_txt", "component": { "Text": { "text": { "literalString": f"Device: {selected_device['name']}" } } } },
            { "id": "device_price_txt", "component": { "Text": { "text": { "literalString": device_price_str } } } },
        ])
        summary_children.append("device_summary_row")
        
    if discount_percent > 0:
        total_savings = (plan_price + device_price) * (discount_percent / 100)
        components.extend([
            { "id": "savings_row", "component": { "Row": { "children": { "explicitList": ["savings_label", "savings_val"] }, "distribution": "spaceBetween" } } },
            { "id": "savings_label", "component": { "Text": { "text": { "literalString": "Total Savings:" }, "usageHint": "h4" } } },
            { "id": "savings_val", "component": { "Text": { "text": { "literalString": f"-${round(total_savings, 2)}" }, "usageHint": "h4" } } },
        ])
        summary_children.append("savings_row")

    components.extend([
        { "id": "total_row", "component": { "Row": { "children": { "explicitList": ["total_label", "total_val"] }, "distribution": "spaceBetween" } } },
        { "id": "total_label", "component": { "Text": { "text": { "literalString": "Total Due Today:" }, "usageHint": "h3" } } },
        { "id": "total_val", "component": { "Text": { "text": { "literalString": f"${totals['total_first_month']}" }, "usageHint": "h3" } } },
        
        { "id": "place_order_btn", "component": { "Button": { "child": "btn_txt", "primary": True, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Place my order."}}, {"key": "action", "value": {"literalString": "place_order"}}] } } } },
        { "id": "btn_txt", "component": { "Text": { "text": { "literalString": "Place Order" } } } }
    ])
    summary_children.extend(["total_row", "place_order_btn"])
    
    for comp in components:
        if comp["id"] == "summary_col":
            comp["component"]["Column"]["children"]["explicitList"] = summary_children
            break
            
    payload = {
        "a2ui_messages": [
            { "beginRendering": { "surfaceId": "order_summary", "root": "summary_card" } },
            { "surfaceUpdate": { "surfaceId": "order_summary", "components": components } }
        ]
    }
    
    return f"Please review your order summary:\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def show_order_confirmation_ui(order_id: str, delivery_date: str) -> str:
    """Generates A2UI JSON for order confirmation and returns it as a string with the delimiter."""
    components = [
        { "id": "conf_card", "component": { "Card": { "child": "conf_col" } } },
        { "id": "conf_col", "component": { "Column": { "children": { "explicitList": ["conf_title", "conf_msg", "order_id_txt", "delivery_txt"] } } } },
        { "id": "conf_title", "component": { "Text": { "text": { "literalString": "Order Confirmed!" }, "usageHint": "h2" } } },
        { "id": "conf_msg", "component": { "Text": { "text": { "literalString": "Thank you for your order." } } } },
        { "id": "order_id_txt", "component": { "Text": { "text": { "literalString": f"Order ID: {order_id}" }, "usageHint": "h4" } } },
        { "id": "delivery_txt", "component": { "Text": { "text": { "literalString": f"Expected Delivery: {delivery_date}" } } } }
    ]
    
    payload = {
        "a2ui_messages": [
            { "beginRendering": { "surfaceId": "order_confirmation", "root": "conf_card" } },
            { "surfaceUpdate": { "surfaceId": "order_confirmation", "components": components } }
        ]
    }
    
    return f"Your order is confirmed!\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def show_greeting_ui() -> str:
    """Generates A2UI JSON for the greeting screen."""
    components = [
        { "id": "root_card", "component": { "Card": { "child": "card_col" } } },
        { "id": "card_col", "component": { "Column": { "children": { "explicitList": ["greeting_txt", "cb_plans", "cb_devices", "start_btn_row"] } } } },
        { "id": "greeting_txt", "component": { "Text": { "text": { "literalString": "Hi! I am the Phone Plan Concierge. What are you shopping for today?" }, "usageHint": "h2" } } },
        { "id": "cb_plans", "component": { "CheckBox": { "label": { "literalString": "Phone Plans" }, "value": {"path": "shop_plans"} } } },
        { "id": "cb_devices", "component": { "CheckBox": { "label": { "literalString": "Devices" }, "value": {"path": "shop_devices"} } } },
        { "id": "start_btn_row", "component": { "Row": { "children": { "explicitList": ["start_btn"] }, "distribution": "end" } } },
        { "id": "start_btn", "component": { "Button": { "child": "start_txt", "primary": True, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "I have selected what I am shopping for. Let's begin."}}, {"key": "shop_plans", "value": {"path": "shop_plans"}}, {"key": "shop_devices", "value": {"path": "shop_devices"}}] } } } },
        { "id": "start_txt", "component": { "Text": { "text": { "literalString": "Start Shopping" } } } }
    ]
    
    payload = {
        "a2ui_messages": [
            { "beginRendering": { "surfaceId": "main", "root": "root_card" } },
            { "surfaceUpdate": { "surfaceId": "main", "components": components } },
            { "dataModelUpdate": { "surfaceId": "main", "path": "/", "contents": [ { "key": "shop_plans", "valueBoolean": True }, { "key": "shop_devices", "valueBoolean": True } ] } }
        ]
    }
    return f"Hi! I can help you find phone plans.\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def show_needs_assessment_ui() -> str:
    """Generates A2UI JSON for the needs assessment screen."""
    components = [
        { "id": "form_col", "component": { "Column": { "children": { "explicitList": ["title_txt", "data_slider", "intl_cb", "budget_tf", "submit_btn"] }, "distribution": "start", "alignment": "start" } } },
        { "id": "title_txt", "component": { "Text": { "text": { "literalString": "Tell me about your phone plan needs." }, "usageHint": "h3" } } },
        { "id": "data_slider", "component": { "Slider": { "value": {"path": "data_gb"}, "minValue": 0, "maxValue": 100 } } },
        { "id": "intl_cb", "component": { "CheckBox": { "label": { "literalString": "Needs International Calling?" }, "value": {"path": "intl_calling"} } } },
        { "id": "budget_tf", "component": { "TextField": { "label": { "literalString": "Max Monthly Budget ($)" }, "text": {"path": "budget"}, "textFieldType": "shortText" } } },
        { "id": "submit_btn", "component": { "Button": { "child": "btn_txt", "primary": True, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Find a match for my needs."}}, {"key": "data_gb", "value": {"path": "data_gb"}}, {"key": "intl_calling", "value": {"path": "intl_calling"}}, {"key": "budget", "value": {"path": "budget"}}] } } } },
        { "id": "btn_txt", "component": { "Text": { "text": { "literalString": "Find Match" } } } }
    ]
    
    payload = {
        "a2ui_messages": [
            { "beginRendering": { "surfaceId": "needs_assessment", "root": "form_col" } },
            { "surfaceUpdate": { "surfaceId": "needs_assessment", "components": components } },
            { "dataModelUpdate": { "surfaceId": "needs_assessment", "path": "/", "contents": [ { "key": "data_gb", "valueNumber": 5 }, { "key": "intl_calling", "valueBoolean": False }, {"key": "budget", "valueString": ""} ] } }
        ]
    }
    return f"Let's figure out what you need:\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def create_order_and_show_ui(plan_id: str, device_id: Optional[str] = None, applied_discount: float = 0.0) -> str:
    """Finalizes the purchase and returns the A2UI JSON for order confirmation.
    
    Use this tool when the user confirms they want to place the order. It guarantees correct UI rendering.
    """
    res = tools.create_order(plan_id, device_id, applied_discount)
    if res["status"] == "SUCCESS":
        return show_order_confirmation_ui(res["order_id"], res["expected_delivery"])
    return f"Failed to create order: {res.get('reason', 'Unknown error')}"
