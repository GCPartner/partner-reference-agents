import base64
import json
import os
import jsonschema
from typing import List, Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext

from vertexai.preview.generative_models import Part
try:
    from . import tools # Import original tools
except ImportError:
    import tools

def get_provider_logo_url(provider_name: str) -> str:
    prov_lower = provider_name.lower()
    if "at&t" in prov_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/5/5c/AT%26T-logo_2016.png"
    elif "verizon" in prov_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Verizon_2024.svg/1280px-Verizon_2024.svg.png"
    elif "t-mobile" in prov_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/T-Mobile_US_Logo_2022_RGB_Magenta_on_Transparent.svg/1280px-T-Mobile_US_Logo_2022_RGB_Magenta_on_Transparent.svg.png"
    return "https://placehold.co/100x100"

def get_device_image_url(device_name: str) -> str:
    name_lower = device_name.lower()
    if "pixel" in name_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Google_Pixel_9_%28Obsidian%29_front.svg/500px-Google_Pixel_9_%28Obsidian%29_front.svg.png"
    elif "iphone" in name_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Front_of_iPhone_15_Pro_Max.jpg/500px-Front_of_iPhone_15_Pro_Max.jpg"
    elif "samsung" in name_lower or "galaxy" in name_lower:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Samsung-Galaxy-S24-Ultra-Front.jpg/960px-Samsung-Galaxy-S24-Ultra-Front.jpg"
    return "https://placehold.co/100x100"



def show_discount_request_ui() -> str:
    version = get_a2ui_version()
    root_id = "root" if version == "v0.9" else "discount_card"
    
    components = [
        make_card(root_id, "discount_col", style={"padding": "15px", "border": "1px solid #FAE8FF", "borderRadius": "8px", "backgroundColor": "#FDF4FF"}, version=version),
        make_column("discount_col", ["discount_txt", "discount_btns"], version=version),
        make_text("discount_txt", "Would you like me to request a manager discount for you?", variant="h4", style={"color": "#4F46E5", "fontWeight": "bold", "marginBottom": "12px"}, version=version),
        make_row("discount_btns", ["yes_btn", "no_btn"], version=version),
        make_button("yes_btn", "Yes", variant="primary", action={
            "name": "submit",
            "context": {"message": "Yes, please request a discount."}
        }, style={"backgroundColor": "#7C3AED", "color": "white", "borderRadius": "6px", "padding": "8px 16px"}, version=version),
        make_button_label("yes_btn", "Yes", version=version),
        make_button("no_btn", "No", variant="default", action={
            "name": "submit",
            "context": {"message": "No, thanks."}
        }, style={"backgroundColor": "white", "color": "#7C3AED", "border": "1px solid #FAE8FF", "borderRadius": "6px", "padding": "8px 16px"}, version=version),
        make_button_label("no_btn", "No", version=version)
    ]
    components = [c for c in components if c is not None]
    
    payload = build_payload("discount_request", root_id, components, version=version)
    
    return f"Would you like me to request a manager discount for you?\n---a2ui_JSON---\n{json.dumps(payload)}\n"

COMPONENT_PREFIX = "Material"

def get_a2ui_version() -> str:
    return os.environ.get("A2UI_VERSION", "v0.9")

def make_card(id: str, child: str, weight: float = None, style: Optional[dict] = None, version: str = "v0.9") -> dict:
    if version == "v0.9":
        res = {
            "id": id,
            "component": f"{COMPONENT_PREFIX}Card",
        }
        if COMPONENT_PREFIX == "Material":
            res["children"] = [child]
        else:
            res["child"] = child
    else:
        res = {
            "id": id,
            "component": {
                "Card": {
                    "child": child
                }
            }
        }
    if weight is not None:
        res["weight"] = weight
    if style is not None:
        res["style"] = style
    return res

def make_column(id: str, children: list, justify: str = "start", align: str = "start", weight: float = None, style: Optional[dict] = None, version: str = "v0.9") -> dict:
    if version == "v0.9":
        res = {
            "id": id,
            "component": f"{COMPONENT_PREFIX}Column",
            "children": children
        }
        if justify != "start":
            res["justify"] = justify
        if align != "start":
            res["align"] = align
    else:
        res = {
            "id": id,
            "component": {
                "Column": {
                    "children": { "explicitList": children },
                    "distribution": justify,
                    "alignment": align
                }
            }
        }
    if weight is not None:
        res["weight"] = weight
    if style is not None:
        res["style"] = style
    return res

def make_row(id: str, children: list, justify: str = "start", align: str = "start", gap: str = None, weight: float = None, style: Optional[dict] = None, version: str = "v0.9") -> dict:
    if version == "v0.9":
        res = {
            "id": id,
            "component": f"{COMPONENT_PREFIX}Row",
            "children": children
        }
        if justify != "start":
            res["justify"] = justify
        if align != "start":
            res["align"] = align
        if gap:
            res["gap"] = gap
    else:
        row_props = {
            "children": { "explicitList": children },
            "distribution": justify,
            "alignment": align
        }
        if gap:
            row_props["gap"] = gap
        res = {
            "id": id,
            "component": {
                "Row": row_props
            }
        }
    if weight is not None:
        res["weight"] = weight
    if style is not None:
        res["style"] = style
    return res

def make_text(id: str, text: str | dict, variant: str = "body", weight: float = None, style: Optional[dict] = None, version: str = "v0.9") -> dict:
    if version == "v0.9":
        res = {
            "id": id,
            "component": f"{COMPONENT_PREFIX}Text",
            "text": text,
            "variant": variant
        }
    else:
        text_obj = {}
        if isinstance(text, dict) and "path" in text:
            text_obj["path"] = text["path"]
        else:
            text_obj["literalString"] = text
        res = {
            "id": id,
            "component": {
                "Text": {
                    "text": text_obj,
                    "usageHint": variant
                }
            }
        }
    if weight is not None:
        res["weight"] = weight
    if style is not None:
        res["style"] = style
    return res

def make_image(id: str, url: str | dict, fit: str = "fill", variant: str = "mediumFeature", weight: float = None, width: Optional[str] = None, height: Optional[str] = None, style: Optional[dict] = None, version: str = "v0.9") -> dict:
    if version == "v0.9":
        style_obj = {}
        if style is not None:
            style_obj.update(style)
        if width is not None:
            style_obj["width"] = width
        if height is not None:
            style_obj["height"] = height
            
        res = {
            "id": id,
            "component": "Image",
            "url": url,
            "fit": fit,
            "variant": variant
        }
        if style_obj:
            res["style"] = style_obj
    else:
        url_obj = {}
        if isinstance(url, dict) and "path" in url:
            url_obj["path"] = url["path"]
        else:
            url_obj["literalString"] = url
        res = {
            "id": id,
            "component": {
                "Image": {
                    "url": url_obj,
                    "fit": fit,
                    "usageHint": variant
                }
            }
        }
        if style is not None:
            res["style"] = style
    if weight is not None:
        res["weight"] = weight
    return res

def make_checkbox(id: str, label: str | dict, value: dict | bool, weight: float = None, version: str = "v0.9") -> dict:
    if version == "v0.9":
        res = {
            "id": id,
            "component": "MaterialCheckbox",
            "label": label,
            "value": value
        }
    else:
        label_obj = {}
        if isinstance(label, dict) and "path" in label:
            label_obj["path"] = label["path"]
        else:
            label_obj["literalString"] = label
            
        value_obj = {}
        if isinstance(value, dict) and "path" in value:
            value_obj["path"] = value["path"]
        else:
            value_obj["literalBoolean"] = value
            
        res = {
            "id": id,
            "component": {
                "CheckBox": {
                    "label": label_obj,
                    "value": value_obj
                }
            }
        }
    if weight is not None:
        res["weight"] = weight
    return res

def make_textfield(id: str, label: str | dict, value: dict | str, variant: str = "shortText", weight: float = None, style: Optional[dict] = None, version: str = "v0.9") -> dict:
    if version == "v0.9":
        res = {
            "id": id,
            "component": "MaterialInput",
            "label": label,
            "value": value,
            "variant": variant
        }
    else:
        label_obj = {}
        if isinstance(label, dict) and "path" in label:
            label_obj["path"] = label["path"]
        else:
            label_obj["literalString"] = label
            
        text_obj = {}
        if isinstance(value, dict) and "path" in value:
            text_obj["path"] = value["path"]
        else:
            text_obj["literalString"] = value
            
        res = {
            "id": id,
            "component": {
                "TextField": {
                    "label": label_obj,
                    "text": text_obj,
                    "textFieldType": variant
                }
            }
        }
    if weight is not None:
        res["weight"] = weight
    if style is not None:
        res["style"] = style
    return res

def make_select(id: str, label: str, value: dict | str, options: list[dict], weight: float = None, version: str = "v0.9") -> dict:
    if version == "v0.9":
        res = {
            "id": id,
            "component": "MaterialSelect",
            "label": label,
            "value": value,
            "options": options
        }
    else:
        # Fallback to MultipleChoice for v0.8
        res = {
            "id": id,
            "component": {
                "MultipleChoice": {
                    "selections": value,
                    "options": options
                }
            }
        }
    if weight is not None:
        res["weight"] = weight
    return res

def make_slider(id: str, value: dict | float, min: float, max: float, label: Optional[str] = None, weight: float = None, style: Optional[dict] = None, version: str = "v0.9") -> dict:
    if version == "v0.9":
        res = {
            "id": id,
            "component": "Slider",
            "value": value,
            "min": min,
            "max": max
        }
        if label is not None:
            res["label"] = label
            
        # Add default styling to stretch slider to full width
        if style is None:
            style = {"width": "100%"}
        else:
            style = dict(style)
            if "width" not in style:
                style["width"] = "100%"
    else:
        value_obj = {}
        if isinstance(value, dict) and "path" in value:
            value_obj["path"] = value["path"]
        else:
            value_obj["literalNumber"] = value
            
        res = {
            "id": id,
            "component": {
                "Slider": {
                    "value": value_obj,
                    "minValue": min,
                    "maxValue": max
                }
            }
        }
    if weight is not None:
        res["weight"] = weight
    if style is not None:
        res["style"] = style
    return res

def make_button(id: str, label: str, variant: str = "primary", action: dict = None, weight: float = None, style: Optional[dict] = None, version: str = "v0.9") -> dict:
    if action is None:
        action = {"name": "submit", "context": {}}
        
    action_name = action.get("name", "submit")
    context_dict = action.get("context", {})
    
    if version == "v0.9":
        event_obj = {
            "name": action_name
        }
        if context_dict:
            event_obj["context"] = context_dict
        res = {
            "id": id,
            "component": f"{COMPONENT_PREFIX}Button",
            "variant": variant,
            "action": {
                "event": event_obj
            }
        }
        if COMPONENT_PREFIX == "Material":
            res["label"] = label
        else:
            res["child"] = f"{id}_label"
    else:
        primary_val = (variant == "primary")
        context_arr = []
        for k, v in context_dict.items():
            val_obj = {}
            if isinstance(v, dict) and "path" in v:
                val_obj["path"] = v["path"]
            elif isinstance(v, bool):
                val_obj["literalBoolean"] = v
            elif isinstance(v, (int, float)):
                val_obj["literalNumber"] = v
            else:
                val_obj["literalString"] = str(v)
            context_arr.append({
                "key": k,
                "value": val_obj
            })
            
        action_obj = {
            "name": action_name
        }
        if context_arr:
            action_obj["context"] = context_arr
            
        res = {
            "id": id,
            "component": {
                "Button": {
                    "child": f"{id}_label",
                    "primary": primary_val,
                    "action": action_obj
                }
            }
        }
    if weight is not None:
        res["weight"] = weight
    if style is not None:
        res["style"] = style
    return res

def make_button_label(btn_id: str, label: str, version: str = "v0.9") -> Optional[dict]:
    if COMPONENT_PREFIX == "Material":
        return None
    return make_text(f"{btn_id}_label", label, version=version)

def build_payload(surface_id: str, root_id: str, components: list, data_model: dict = None, version: str = "v0.9") -> dict:
    if version == "v0.9":
        messages = [
            {
                "version": "v0.9",
                "deleteSurface": {
                    "surfaceId": surface_id
                }
            },
            {
                "version": "v0.9",
                "createSurface": {
                    "surfaceId": surface_id,
                    "catalogId": "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json"
                }
            },
            {
                "version": "v0.9",
                "updateComponents": {
                    "surfaceId": surface_id,
                    "components": components
                }
            }
        ]
        if data_model:
            messages.append({
                "version": "v0.9",
                "updateDataModel": {
                    "surfaceId": surface_id,
                    "path": "/",
                    "value": data_model
                }
            })
        payload = {
            "messages": messages
        }
        validate_a2ui(payload, version=version)
        return payload
    else:
        messages = [
            {
                "deleteSurface": {
                    "surfaceId": surface_id
                }
            },
            {
                "beginRendering": {
                    "surfaceId": surface_id,
                    "root": root_id
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": surface_id,
                    "components": components
                }
            }
        ]
        if data_model:
            contents = []
            for k, v in data_model.items():
                if isinstance(v, bool):
                    contents.append({"key": k, "valueBoolean": v})
                elif isinstance(v, (int, float)):
                    contents.append({"key": k, "valueNumber": v})
                else:
                    contents.append({"key": k, "valueString": str(v)})
            messages.append({
                "dataModelUpdate": {
                    "surfaceId": surface_id,
                    "path": "/",
                    "contents": contents
                }
            })
        payload = {
            "messages": messages
        }
        validate_a2ui(payload, version=version)
        return payload

def validate_a2ui(parsed_json: Any, version: str = "v0.9"):
    """Validates the parsed A2UI payload against the schema."""
    dir_path = os.path.dirname(__file__)
    
    if version == "v0.9":
        with open(os.path.join(dir_path, 'common_types_v0_9.json'), 'r') as f:
            common_types = json.load(f)
        with open(os.path.join(dir_path, 'gemini_enterprise_composite_catalog.json'), 'r') as f:
            catalog_schema = json.load(f)
            
        try:
            from a2ui.core.catalog.catalog import Catalog
            from a2ui.core.validating.catalog_schema_validator import CatalogSchemaValidator
            from a2ui.core.validating.validator import A2uiValidator
            
            catalog = Catalog.from_json(catalog_schema, "0.9", catalog_id="https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json")
            schema_validator = CatalogSchemaValidator(catalog, common_types)
            import logging
            logger = logging.getLogger("a2ui_tools")
            logger.info("[DEBUG validate_a2ui] parsed_json type: %s", type(parsed_json))
            if isinstance(parsed_json, dict):
                logger.info("[DEBUG validate_a2ui] parsed_json keys: %s", list(parsed_json.keys()))
            
            validator = A2uiValidator()
            payload_to_validate = parsed_json
            if isinstance(parsed_json, dict) and "messages" in parsed_json:
                logger.info("[DEBUG validate_a2ui] Extracting messages list from parsed_json dict")
                payload_to_validate = parsed_json["messages"]
                
            logger.info("[DEBUG validate_a2ui] payload_to_validate type: %s", type(payload_to_validate))
            validator.validate(schema_validator, payload_to_validate)
        except ImportError:
            import logging
            logging.getLogger("a2ui_tools").warning("a2ui validation package not found; bypassing schema validation.")
            pass
    else:
        schema_path = os.path.join(dir_path, 'a2ui_schema.json')
        with open(schema_path, 'r') as f:
            a2ui_schema = json.load(f)
            
        if isinstance(parsed_json, dict) and "a2ui_messages" in parsed_json:
            messages_list = parsed_json["a2ui_messages"]
        elif isinstance(parsed_json, list):
            messages_list = parsed_json
        else:
            messages_list = [parsed_json]
            
        for msg in messages_list:
            jsonschema.validate(instance=msg, schema=a2ui_schema)

def render_ui(a2ui_json: str, tool_context: ToolContext = None):
    """Submits the A2UI JSON payload to the client screen to dynamically render user interfaces like forms, cards, and lists.
    
    CRITICAL INSTRUCTIONS FOR LLM:
    - You MUST call this tool INSTEAD of printing raw JSON codeblocks into the chat stream.
    - Pass the entire A2UI JSON payload as a string to the `a2ui_json` parameter.
    - If you receive a JSON validation error back from this tool, YOU MUST fix your schema based on the error and call the tool again!
    
    Args:
        a2ui_json: A valid JSON string containing the A2UI messages array or wrapper object.
    Returns:
        A binary Part object containing the UI payload for native rendering.
    """
    version = get_a2ui_version()
    try:
        a2ui_messages = json.loads(a2ui_json)
        validate_a2ui(a2ui_messages, version)
        return Part.from_data(data=a2ui_json.encode('utf-8'), mime_type="application/json+a2ui")
        
    except json.JSONDecodeError as e:
        return f"CRITICAL SYNTAX ERROR in your JSON string:\nError: {e.msg}\nLocation: line {e.lineno}, col {e.colno}\nRemedy: Check for extra/missing braces, commas, or quotes near the error location, fix the JSON, and call `render_ui` again!"

    except jsonschema.exceptions.ValidationError as e:
        path_str = ' -> '.join(str(p) for p in e.path) if e.path else 'Root Level'
        return f"CRITICAL VALIDATION ERROR in your A2UI message against version {version}:\nError: {e.message}\nPath: {path_str}\nRemedy: Fix the JSON structure based on the schema requirements and call `render_ui` again!"
        
    except Exception as e:
        return f"System Error processing A2UI payload: {str(e)}"

def show_plans_ui(plans: List[Dict[str, Any]]) -> str:
    """Generates A2UI JSON for a list of plans and returns it as a string with the delimiter.
    
    Args:
        plans: List of plan dictionaries.
    """
    print(f"Calling show_plans_ui with {len(plans)} plans")
    version = get_a2ui_version()
    root_id = "root" if version == "v0.9" else "plan_select_card"
    
    components = [
        make_card(root_id, "plan_select_col", style={"padding": "15px", "border": "1px solid #FAE8FF", "borderRadius": "8px", "backgroundColor": "#FDF4FF"}, version=version),
        make_column("plan_select_col", ["plan_title", "plan_list_col"], version=version),
        make_text("plan_title", "Please select a plan:", variant="h3", style={"color": "#4F46E5"}, version=version)
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
        
        logo_url = get_provider_logo_url(plan.get("provider", ""))
             
        logo_container_id = f"plan_logo_container_{i}"
        
        components.extend([
            make_card(item_id, row_id, style={"padding": "10px", "border": "1px solid #FAE8FF", "borderRadius": "8px", "backgroundColor": "white"}, version=version),
            make_row(row_id, [logo_id, details_id, btn_id], justify="spaceBetween", align="center", version=version),
            make_image(logo_id, logo_url, fit="contain", variant="smallFeature", weight=1, version=version),
            make_column(details_id, [name_id, price_id], weight=3, version=version),
            make_text(name_id, f"{plan['name']} ({plan['provider']})", variant="body", version=version),
            make_text(price_id, f"${plan['price']}/mo", variant="caption", version=version),
            make_button(btn_id, "Select", variant="primary", action={
                "name": "submit",
                "context": {
                    "message": f"I select the {plan['name']} plan.",
                    "selected_plan_id": plan['id']
                }
            }, weight=1, style={"backgroundColor": "#7C3AED", "color": "white"}, version=version),
            make_button_label(btn_id, "Select", version=version)
        ])
        
    components.append(make_column("plan_list_col", plan_item_ids, version=version))
    components = [c for c in components if c is not None]
    
    payload = build_payload("plan_selection", root_id, components, version=version)
    return f"Here are the plans that match your needs:\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def show_devices_ui(devices: List[Dict[str, Any]]) -> str:
    """Generates A2UI JSON for a list of devices and returns it as a string with the delimiter.
    
    Args:
        devices: List of device dictionaries.
    """
    print(f"Calling show_devices_ui with {len(devices)} devices")
    version = get_a2ui_version()
    root_id = "root" if version == "v0.9" else "device_select_card"
    
    components = [
        make_card(root_id, "device_select_col", style={"padding": "15px", "border": "1px solid #FAE8FF", "borderRadius": "8px", "backgroundColor": "#FDF4FF"}, version=version),
        make_column("device_select_col", ["device_title", "device_list_col"], version=version),
        make_text("device_title", "Please select a device:", variant="h3", style={"color": "#4F46E5"}, version=version)
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
             
        img_container_id = f"device_img_container_{i}"
        
        components.extend([
            make_card(item_id, row_id, style={"padding": "10px", "border": "1px solid #FAE8FF", "borderRadius": "8px", "backgroundColor": "white"}, version=version),
            make_row(row_id, [img_id, details_id, btn_id], justify="spaceBetween", align="center", version=version),
            make_image(img_id, img_url, fit="contain", variant="smallFeature", weight=1, version=version),
            make_column(details_id, [name_id, price_id], weight=3, version=version),
            make_text(name_id, f"{device['name']} ({device['brand']})", variant="body", version=version),
            make_text(price_id, f"${device['price']}", variant="caption", version=version),
            make_button(btn_id, "Select", variant="primary", action={
                "name": "submit",
                "context": {
                    "message": f"I select the {device['name']}.",
                    "selected_device_id": device['id']
                }
            }, weight=1, style={"backgroundColor": "#7C3AED", "color": "white"}, version=version),
            make_button_label(btn_id, "Select", version=version)
        ])
        
    components.append(make_column("device_list_col", device_item_ids, version=version))
    components = [c for c in components if c is not None]
    
    payload = build_payload("device_selection", root_id, components, version=version)
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
    version = get_a2ui_version()
    surface_id = "order_summary"
    if discount_percent > 0:
        surface_id = "order_summary_discounted"
    root_id = "root" if version == "v0.9" else f"{surface_id}_card"
    
    all_plans = tools.search_plans()
    selected_plan = next((p for p in all_plans if p["id"] == plan_id), None)
    
    plan_logo_url = get_provider_logo_url(selected_plan.get("provider", "")) if selected_plan else "https://placehold.co/100x100"

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
        make_card(root_id, "summary_col", style={"padding": "15px", "border": "1px solid #FAE8FF", "borderRadius": "8px", "backgroundColor": "#FDF4FF"}, version=version),
        make_column("summary_col", ["summary_title", "plan_summary_row"], version=version),
        make_text("summary_title", "Order Summary", variant="h3", style={"color": "#4F46E5"}, version=version),
        make_row("plan_summary_row", ["plan_logo", "plan_txt_col"], align="center", version=version),
        make_image("plan_logo", plan_logo_url, fit="contain", variant="smallFeature", weight=1, version=version),
        make_column("plan_txt_col", ["plan_name_txt", "plan_price_txt"], weight=3, version=version),
        make_text("plan_name_txt", f"Plan: {selected_plan['name']}" if selected_plan else "Unknown Plan", version=version),
        make_text("plan_price_txt", plan_price_str, version=version),
    ]
    
    summary_children = ["summary_title", "plan_summary_row"]
    
    if selected_device:
        components.extend([
            make_row("device_summary_row", ["device_img", "device_txt_col"], align="center", version=version),
            make_image("device_img", device_img_url, fit="contain", variant="smallFeature", weight=1, version=version),
            make_column("device_txt_col", ["device_name_txt", "device_price_txt"], weight=3, version=version),
            make_text("device_name_txt", f"Device: {selected_device['name']}", version=version),
            make_text("device_price_txt", device_price_str, version=version),
        ])
        summary_children.append("device_summary_row")
        
    if discount_percent > 0:
        total_savings = (plan_price + device_price) * (discount_percent / 100)
        components.extend([
            make_row("savings_row", ["savings_label", "savings_val"], justify="spaceBetween", version=version),
            make_text("savings_label", "Total Savings:", variant="h4", style={"color": "#7C3AED"}, version=version),
            make_text("savings_val", f"-${round(total_savings, 2)}", variant="h4", style={"color": "#7C3AED"}, version=version),
        ])
        summary_children.append("savings_row")

    components.extend([
        make_row("total_row", ["total_label", "total_val"], justify="spaceBetween", version=version),
        make_text("total_label", "Total Due Today:", variant="h3", style={"color": "#4F46E5"}, version=version),
        make_text("total_val", f"${totals['total_first_month']}", variant="h3", style={"color": "#4F46E5"}, version=version),
        make_button("place_order_btn", "Place Order", variant="primary", action={
            "name": "submit",
            "context": {"message": "Place my order.", "action": "place_order"}
        }, style={"backgroundColor": "#7C3AED", "color": "white"}, version=version),
        make_button_label("place_order_btn", "Place Order", version=version)
    ])
    summary_children.extend(["total_row", "place_order_btn"])
    
    for comp in components:
        if comp is not None and comp["id"] == "summary_col":
            if version == "v0.9":
                comp["children"] = summary_children
            else:
                comp["component"]["Column"]["children"]["explicitList"] = summary_children
            break
            
    components = [c for c in components if c is not None]
    payload = build_payload(surface_id, root_id, components, version=version)
    return f"Please review your order summary:\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def show_order_confirmation_ui(order_id: str, delivery_date: str) -> str:
    """Generates A2UI JSON for order confirmation and returns it as a string with the delimiter."""
    version = get_a2ui_version()
    root_id = "root" if version == "v0.9" else "conf_card"
    
    components = [
        make_card(root_id, "conf_col", version=version),
        make_column("conf_col", ["conf_title", "conf_msg", "order_id_txt", "delivery_txt"], version=version),
        make_text("conf_title", "Order Confirmed!", variant="h2", version=version),
        make_text("conf_msg", "Thank you for your order.", version=version),
        make_text("order_id_txt", f"Order ID: {order_id}", variant="h4", version=version),
        make_text("delivery_txt", f"Expected Delivery: {delivery_date}", version=version)
    ]
    
    payload = build_payload("order_confirmation", root_id, components, version=version)
    return f"Your order is confirmed!\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def show_greeting_ui() -> str:
    """Generates A2UI JSON for the greeting screen."""
    version = get_a2ui_version()
    root_id = "root" if version == "v0.9" else "root_card"
    
    components = [
        make_card(root_id, "card_col", style={"padding": "15px", "border": "1px solid #FAE8FF", "borderRadius": "8px", "backgroundColor": "#FDF4FF"}, version=version),
        make_column("card_col", ["greeting_txt", "cb_plans", "cb_devices", "start_btn_row"], version=version),
        make_text("greeting_txt", "Hi! I am the Phone Plan Concierge. What are you shopping for today?", variant="h2", style={"color": "#4F46E5"}, version=version),
        make_checkbox("cb_plans", "Phone Plans", {"path": "/shop_plans"}, version=version),
        make_checkbox("cb_devices", "Devices", {"path": "/shop_devices"}, version=version),
        make_row("start_btn_row", ["start_btn"], justify="end", version=version),
        make_button("start_btn", "Start Shopping", variant="primary", action={
            "name": "submit",
            "context": {
                "message": "I have selected what I am shopping for. Let's begin.",
                "shop_plans": {"path": "/shop_plans"},
                "shop_devices": {"path": "/shop_devices"}
            }
        }, style={"backgroundColor": "#7C3AED", "color": "white"}, version=version),
        make_button_label("start_btn", "Start Shopping", version=version)
    ]
    components = [c for c in components if c is not None]
    
    payload = build_payload("main", root_id, components, data_model={
        "shop_plans": True,
        "shop_devices": True
    }, version=version)
    return f"Hi! I can help you find phone plans.\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def show_needs_assessment_ui() -> str:
    """Generates A2UI JSON for the needs assessment screen."""
    version = get_a2ui_version()
    root_id = "root" if version == "v0.9" else "form_card"
    
    components = [
        make_card(root_id, "form_col", style={"padding": "15px", "border": "1px solid #FAE8FF", "borderRadius": "8px", "backgroundColor": "#FDF4FF"}, version=version),
        make_column("form_col", ["title_txt", "data_slider", "intl_cb", "budget_tf", "submit_btn"], justify="start", align="stretch", version=version),
        make_text("title_txt", "Tell me about your phone plan needs.", variant="h3", style={"color": "#4F46E5", "marginBottom": "15px"}, version=version),
        
        # Native Slider component displays the label/value header automatically in v0.9 basic Slider
        make_slider("data_slider", {"path": "data_gb"}, min=0, max=100, version=version),
        
        make_checkbox("intl_cb", "Needs International Calling?", {"path": "intl_calling"}, version=version),
        make_textfield("budget_tf", "Max Monthly Budget ($)", {"path": "budget"}, variant="shortText", version=version),
        make_button("submit_btn", "Find Match", variant="primary", action={
            "name": "submit",
            "context": {
                "message": "Find a match for my needs.",
                "data_gb": {"path": "data_gb"},
                "intl_calling": {"path": "intl_calling"},
                "budget": {"path": "budget"}
            }
        }, style={"backgroundColor": "#7C3AED", "color": "white", "marginTop": "15px"}, version=version),
        make_button_label("submit_btn", "Find Match", version=version)
    ]
    components = [c for c in components if c is not None]
    
    payload = build_payload("needs_assessment", root_id, components, data_model={
        "data_gb": 45.0,
        "intl_calling": False,
        "budget": ""
    }, version=version)
    return f"Let's figure out what you need:\n---a2ui_JSON---\n{json.dumps(payload)}\n"

def create_order_and_show_ui(plan_id: str, device_id: Optional[str] = None, applied_discount: float = 0.0) -> str:
    """Finalizes the purchase and returns the A2UI JSON for order confirmation.
    
    Use this tool when the user confirms they want to place the order. It guarantees correct UI rendering.
    """
    res = tools.create_order(plan_id, device_id, applied_discount)
    if res["status"] == "SUCCESS":
        return show_order_confirmation_ui(res["order_id"], res["expected_delivery"])
    return f"Failed to create order: {res.get('reason', 'Unknown error')}"
