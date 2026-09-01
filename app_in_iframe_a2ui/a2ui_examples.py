"""Few-shot prompt examples for app_in_iframe A2UI agent."""

EXAMPLE_URL_FORM = r"""{
  "messages": [
    {
      "version": "v0.9",
      "createSurface": {
        "surfaceId": "url_input_form",
        "catalogId": "https://a2ui.org/specification/v0_9/material_catalog.json",
        "theme": {"primaryColor": "#1A73E8"},
        "sendDataModel": true
      }
    },
    {
      "version": "v0.9",
      "updateComponents": {
        "surfaceId": "url_input_form",
        "components": [
          {"id": "root", "component": "Card", "child": "container"},
          {
            "id": "container",
            "component": "Column",
            "children": ["title_text", "desc_text", "url_field", "submit_btn"]
          },
          {
            "id": "title_text",
            "component": "Text",
            "text": "Application Embedder",
            "usageHint": "header"
          },
          {
            "id": "desc_text",
            "component": "Text",
            "text": "Please enter a web application URL (http:// or https://) to view in-line."
          },
          {
            "id": "url_field",
            "component": "TextField",
            "label": "Application URL",
            "text": {"path": "/app_url"},
            "placeholder": "https://example.com"
          },
          {
            "id": "submit_btn_label",
            "component": "Text",
            "text": "Load Application"
          },
          {
            "id": "submit_btn",
            "component": "Button",
            "child": "submit_btn_label",
            "action": {
              "event": {
                "name": "submit_url",
                "context": {
                  "message": "Load URL from input form",
                  "app_url": {"path": "/app_url"}
                }
              }
            }
          }
        ]
      }
    },
    {
      "version": "v0.9",
      "updateDataModel": {
        "surfaceId": "url_input_form",
        "path": "/",
        "value": {"app_url": ""}
      }
    }
  ]
}"""

EXAMPLE_IFRAME_VIEW = r"""{
  "messages": [
    {
      "version": "v0.9",
      "createSurface": {
        "surfaceId": "app_iframe_view",
        "catalogId": "https://a2ui.org/specification/v0_9/material_catalog.json",
        "theme": {"primaryColor": "#1A73E8"},
        "sendDataModel": true
      }
    },
    {
      "version": "v0.9",
      "updateComponents": {
        "surfaceId": "app_iframe_view",
        "components": [
          {"id": "root", "component": "Card", "child": "container"},
          {
            "id": "container",
            "component": "Column",
            "children": ["header_text", "web_frame", "action_row"]
          },
          {
            "id": "header_text",
            "component": "Text",
            "text": "Embedded Application: https://example.com",
            "usageHint": "header"
          },
          {
            "id": "web_frame",
            "component": "WebFrameUrl",
            "url": {"literalString": "https://example.com"},
            "height": 550
          },
          {
            "id": "action_row",
            "component": "Row",
            "children": ["change_url_btn"]
          },
          {
            "id": "change_url_btn_label",
            "component": "Text",
            "text": "Change URL"
          },
          {
            "id": "change_url_btn",
            "component": "Button",
            "child": "change_url_btn_label",
            "action": {
              "event": {
                "name": "reset_url",
                "context": {
                  "message": "Enter a different application URL"
                }
              }
            }
          }
        ]
      }
    },
    {
      "version": "v0.9",
      "updateDataModel": {
        "surfaceId": "app_iframe_view",
        "path": "/",
        "value": {"current_url": "https://example.com"}
      }
    }
  ]
}"""
