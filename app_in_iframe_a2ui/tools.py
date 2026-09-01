import json
import logging
import re
import urllib.parse
from typing import Dict, Any, List, Optional
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger("app_in_iframe_tools")

COMPOSITE_CATALOG_ID = "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json"


def extract_clean_url(raw_url: str) -> str:
    """Extracts and cleans an HTTP/HTTPS URL from plain text, markdown links, or bracketed text."""
    if not raw_url or not isinstance(raw_url, str):
        return ""
    
    # 1. Match Markdown Link syntax: [text](https://example.com)
    m_md = re.search(r'\[.*?\]\((https?://[^\s\)]+)\)', raw_url)
    if m_md:
        return m_md.group(1).strip()
    
    # 2. Match standard URL pattern
    m = re.search(r'(https?://[^\s\)\]\>\"\']+)', raw_url)
    if m:
        url = m.group(1).rstrip('.,;)]\'">')
        return url.strip()
    
    return raw_url.strip()


def validate_url(url: str) -> bool:
    """Validates that a URL is non-empty and starts with http:// or https://."""
    clean = extract_clean_url(url)
    if not clean:
        return False
    if not (clean.startswith("http://") or clean.startswith("https://")):
        return False
    try:
        parsed = urllib.parse.urlparse(clean)
        return bool(parsed.netloc or parsed.path)
    except Exception:
        return False


def render_intake_ui() -> str:
    """Renders the A2UI v0.9 intake form card with Canvas root prompting for an application URL."""
    messages = [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": "app_embedder",
                "catalogId": COMPOSITE_CATALOG_ID,
                "theme": {
                    "primaryColor": "#1a73e8",
                    "font": "Roboto"
                }
            }
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "app_embedder",
                "components": [
                    {
                        "id": "root",
                        "component": "Canvas",
                        "cardTitle": "Application Embedder",
                        "cardDescription": "Enter an application URL to preview in the canvas",
                        "cardIcon": "open_in_new",
                        "autoOpen": True,
                        "children": ["canvas_card"]
                    },
                    {
                        "id": "canvas_card",
                        "component": "MaterialCard",
                        "appearance": "raised",
                        "children": ["canvas_col"],
                        "style": {
                            "padding": "16px",
                            "borderRadius": "8px"
                        }
                    },
                    {
                        "id": "canvas_col",
                        "component": "MaterialColumn",
                        "children": ["title_text", "desc_text", "url_input", "submit_btn"],
                        "align": "stretch"
                    },
                    {
                        "id": "title_text",
                        "component": "MaterialText",
                        "text": "Application Embedder",
                        "usageHint": "h2"
                    },
                    {
                        "id": "desc_text",
                        "component": "MaterialText",
                        "text": "Please enter a web application URL (http:// or https://) to preview in the canvas:",
                        "usageHint": "body"
                    },
                    {
                        "id": "url_input",
                        "component": "MaterialInput",
                        "label": "Application URL",
                        "placeholder": "https://example.com",
                        "value": {
                            "path": "/app/url"
                        }
                    },
                    {
                        "id": "submit_btn",
                        "component": "MaterialButton",
                        "label": "Load Application",
                        "variant": "raised",
                        "action": {
                            "event": {
                                "name": "submit",
                                "context": {
                                    "message": "Load Application",
                                    "app_url": {
                                        "path": "/app/url"
                                    }
                                }
                            }
                        },
                        "style": {
                            "backgroundColor": "#1a73e8",
                            "color": "white",
                            "marginTop": "12px"
                        }
                    }
                ]
            }
        },
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": "app_embedder",
                "path": "/",
                "value": {
                    "app": {
                        "url": ""
                    }
                }
            }
        }
    ]

    payload = {"messages": messages}
    return f"Please enter the application URL you would like to embed below:\n---a2ui_JSON---\n{json.dumps(payload, indent=2)}"


def render_app_iframe(url: str) -> str:
    """Validates the URL and renders an A2UI v0.9 IFrameUrl component inside a Canvas root.
    
    Args:
        url: The web application URL starting with http:// or https://.
    
    Returns:
        A formatted string containing conversational text and the A2UI v0.9 JSON payload.
    """
    cleaned_url = extract_clean_url(url)
    if not validate_url(cleaned_url):
        return f"Invalid URL: '{cleaned_url}'. Please provide a valid web URL starting with http:// or https://."

    messages = [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": "app_embedder",
                "catalogId": COMPOSITE_CATALOG_ID,
                "theme": {
                    "primaryColor": "#1a73e8",
                    "font": "Roboto"
                }
            }
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "app_embedder",
                "components": [
                    {
                        "id": "root",
                        "component": "Canvas",
                        "cardTitle": "Active Application",
                        "cardDescription": f"Embedded view of {cleaned_url}",
                        "cardIcon": "public",
                        "autoOpen": True,
                        "children": ["url-frame"]
                    },
                    {
                        "id": "url-frame",
                        "component": "IFrameUrl",
                        "url": cleaned_url,
                        "height": 650
                    }
                ]
            }
        }
    ]

    payload = {"messages": messages}
    return f"Here is your embedded application:\n---a2ui_JSON---\n{json.dumps(payload, indent=2)}"
