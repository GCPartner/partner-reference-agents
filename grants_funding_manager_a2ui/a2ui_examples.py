# a2ui_examples.py

INTAKE_FORM_EXAMPLE = r"""[
    { "beginRendering": { "surfaceId": "main", "root": "root_card" } },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          { "id": "root_card", "component": { "Card": { "child": "card_col" } } },
          { "id": "card_col", "component": { "Column": { "children": { "explicitList": ["title_txt", "desc_lbl", "desc_tf", "budget_lbl", "budget_tf", "domain_lbl", "cb_health", "cb_ai", "cb_infra", "cb_cyber", "submit_btn_row"] } } } },
          { "id": "title_txt", "component": { "Text": { "text": { "literalString": "New Funding Proposal" }, "usageHint": "h2" } } },
          
          { "id": "desc_lbl", "component": { "Text": { "text": { "literalString": "Project Description:" }, "usageHint": "h3" } } },
          { "id": "desc_tf", "component": { "TextField": { "text": {"path": "description"}, "label": {"literalString": "Explain the project goal and scope..."}, "textFieldType": "shortText" } } },

          { "id": "budget_lbl", "component": { "Text": { "text": { "literalString": "Estimated Budget ($):" }, "usageHint": "h3" } } },
          { "id": "budget_tf", "component": { "TextField": { "text": {"path": "budget"}, "label": {"literalString": "e.g. 500000"}, "textFieldType": "shortText" } } },

          { "id": "domain_lbl", "component": { "Text": { "text": { "literalString": "Project Domains (Select all that apply):" }, "usageHint": "h3" } } },
          { "id": "cb_health", "component": { "CheckBox": { "label": {"literalString": "Public Health"}, "value": {"path": "domain_health"} } } },
          { "id": "cb_ai", "component": { "CheckBox": { "label": {"literalString": "AI/ML"}, "value": {"path": "domain_ai"} } } },
          { "id": "cb_infra", "component": { "CheckBox": { "label": {"literalString": "Infrastructure"}, "value": {"path": "domain_infra"} } } },
          { "id": "cb_cyber", "component": { "CheckBox": { "label": {"literalString": "Cybersecurity"}, "value": {"path": "domain_cyber"} } } },

          { "id": "submit_btn_row", "component": { "Row": { "children": { "explicitList": ["submit_btn"] }, "distribution": "end" } } },
          { "id": "submit_btn", "component": { "Button": { "child": "submit_btn_txt", "primary": true, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Analyze alignment for this proposal."}}, {"key": "description", "value": {"path": "description"}}, {"key": "budget", "value": {"path": "budget"}}, {"key": "domain_health", "value": {"path": "domain_health"}}, {"key": "domain_ai", "value": {"path": "domain_ai"}}, {"key": "domain_infra", "value": {"path": "domain_infra"}}, {"key": "domain_cyber", "value": {"path": "domain_cyber"}}] } } } },
          { "id": "submit_btn_txt", "component": { "Text": { "text": { "literalString": "Analyze Alignment" } } } }
        ]
      }
    },
    { "dataModelUpdate": { "surfaceId": "main", "path": "/", "contents": [ { "key": "description", "valueString": "" }, { "key": "budget", "valueString": "" }, { "key": "domain_health", "valueBoolean": false }, { "key": "domain_ai", "valueBoolean": false }, { "key": "domain_infra", "valueBoolean": false }, { "key": "domain_cyber", "valueBoolean": false } ] } }
]
"""


REVIEW_PACKAGE_EXAMPLE = r"""[
    { "beginRendering": { "surfaceId": "review", "root": "review_card" } },
    {
      "surfaceUpdate": {
        "surfaceId": "review",
        "components": [
          { "id": "review_card", "component": { "Card": { "child": "review_col" } } },
          { "id": "review_col", "component": { "Column": { "children": { "explicitList": ["review_title", "grant_details", "draft_lbl", "draft_preview", "submit_btn_row"] } } } },
          { "id": "review_title", "component": { "Text": { "text": { "literalString": "Grant Submission Package" }, "usageHint": "h2" } } },
          
          { "id": "grant_details", "component": { "Text": { "text": { "literalString": "Target Grant: [Grant ID] - [Grant Title]" }, "usageHint": "h3" } } },
          
          { "id": "draft_lbl", "component": { "Text": { "text": { "literalString": "Application Draft Preview:" }, "usageHint": "h4" } } },
          { "id": "draft_preview", "component": { "Text": { "text": { "literalString": "..." } } } },
 
          { "id": "submit_btn_row", "component": { "Row": { "children": { "explicitList": ["approve_btn"] }, "distribution": "end" } } },
          { "id": "approve_btn", "component": { "Button": { "child": "approve_btn_txt", "primary": true, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Approve and submit this package."}}] } } } },
          { "id": "approve_btn_txt", "component": { "Text": { "text": { "literalString": "Approve Submission" } } } }
        ]
      }
    }
]
"""

