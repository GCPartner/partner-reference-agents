import json
import logging
import os
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from typing import Any

logger = logging.getLogger(__name__)

def get_a2ui_version() -> str:
    return os.environ.get("A2UI_VERSION", "v0.9")

def _wrap_a2ui_part(a2ui_message: dict) -> types.Part:
    """Wrap a single A2UI message for rendering in adk web."""
    datapart_json = json.dumps({
        "kind": "data",
        "metadata": {"mimeType": "application/json+a2ui"},
        "data": a2ui_message,
    })
    blob_data = (
        b"<a2a_datapart_json>"
        + datapart_json.encode("utf-8")
        + b"</a2a_datapart_json>"
    )
    return types.Part(
        inline_data=types.Blob(
            data=blob_data,
            mime_type="text/plain",
        )
    )

def careconnect_a2ui_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    """Convert a2ui JSON payload inside the text response to rendered components."""
    if not llm_response.content or not llm_response.content.parts:
        return None
        
    new_parts = []
    has_a2ui = False
    
    for part in llm_response.content.parts:
        if not part.text:
            new_parts.append(part)
            continue
            
        text = part.text
        if "---a2ui_JSON---" in text:
            parts_split = text.split("---a2ui_JSON---", 1)
            conversational_text = parts_split[0].strip()
            json_text = parts_split[1].strip()
            
            # Clean JSON string (strip markdown code blocks if any)
            json_text = json_text.lstrip("```json").rstrip("```").strip()
            
            # Keep the conversational text part
            if conversational_text:
                new_parts.append(types.Part(text=conversational_text))
                
            try:
                # Parse JSON payload
                a2ui_data = json.loads(json_text)
                has_a2ui = True
                
                # Check if it's an object with "messages" or "a2ui_messages"
                if isinstance(a2ui_data, dict):
                    if "messages" in a2ui_data:
                        messages = a2ui_data["messages"]
                    elif "a2ui_messages" in a2ui_data:
                        messages = a2ui_data["a2ui_messages"]
                    else:
                        messages = [a2ui_data]
                elif isinstance(a2ui_data, list):
                    messages = a2ui_data
                else:
                    messages = [a2ui_data]
                    
                for msg in messages:
                    new_parts.append(_wrap_a2ui_part(msg))
                    
            except Exception as e:
                logging.error(f"Error parsing A2UI JSON in callback: {e}")
                # Fallback: append original text
                new_parts.append(part)
        else:
            new_parts.append(part)
            
    if has_a2ui:
        logging.info("A2UI callback successfully wrapped A2UI parts.")
        return LlmResponse(
            content=types.Content(role="model", parts=new_parts),
            custom_metadata={"a2a:response": "true"},
        )
        
    return None

def validate_a2ui(parsed_json: Any, version: str = "v0.9"):
    """Validates the parsed A2UI payload against the schema."""
    dir_path = os.path.dirname(__file__)
    
    if version == "v0.9":
        # Load v0.9 schema files
        with open(os.path.join(dir_path, 'common_types_v0_9.json'), 'r') as f:
            common_types = json.load(f)
        with open(os.path.join(dir_path, 'composite_catalog_v0_9.json'), 'r') as f:
            catalog_schema = json.load(f)
            
        from a2ui.core.catalog.catalog import Catalog
        from a2ui.core.validating.catalog_schema_validator import CatalogSchemaValidator
        from a2ui.core.validating.validator import A2uiValidator
        
        catalog = Catalog.from_json(catalog_schema, "0.9", catalog_id="https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json")
        schema_validator = CatalogSchemaValidator(catalog, common_types)
        
        validator = A2uiValidator()
        payload_to_validate = parsed_json
        if isinstance(parsed_json, dict) and "messages" in parsed_json:
            payload_to_validate = parsed_json["messages"]
            
        validator.validate(schema_validator, payload_to_validate)
    else:
        import jsonschema
        schema_path = os.path.join(dir_path, 'a2ui_schema.json')
        with open(schema_path, 'r') as f:
            single_message_schema = json.load(f)
        schema_object = {
            "anyOf": [
                single_message_schema,
                {
                    "type": "array",
                    "items": single_message_schema
                },
                {
                    "type": "object",
                    "properties": {
                        "a2ui_messages": {
                            "type": "array",
                            "items": single_message_schema
                        }
                    },
                    "required": ["a2ui_messages"]
                }
            ]
        }
        jsonschema.validate(instance=parsed_json, schema=schema_object)
