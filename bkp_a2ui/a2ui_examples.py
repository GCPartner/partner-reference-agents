PLAN_CLARIFICATION_EXAMPLE = r"""
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "main", "root": "plan_card" } },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          { "id": "plan_card", "component": { "Card": { "child": "plan_col" } } },
          { "id": "plan_col", "component": { "Column": { "children": { "explicitList": ["title_txt", "hmo_btn", "ppo_btn"] } } } },
          { "id": "title_txt", "component": { "Text": { "text": { "literalString": "Please select your plan type:" }, "usageHint": "h3" } } },
          { "id": "hmo_btn", "component": { "Button": { "child": "hmo_txt", "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "I have HMO plan"}}, {"key": "plan_type", "value": {"literalString": "HMO"}}] } } } },
          { "id": "hmo_txt", "component": { "Text": { "text": { "literalString": "HMO" } } } },
          { "id": "ppo_btn", "component": { "Button": { "child": "ppo_txt", "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "I have PPO plan"}}, {"key": "plan_type", "value": {"literalString": "PPO"}}] } } } },
          { "id": "ppo_txt", "component": { "Text": { "text": { "literalString": "PPO" } } } }
        ]
      }
    }
  ]
}
"""

PROVIDER_LIST_EXAMPLE = r"""
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "main", "root": "provider_list_col" } },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          { "id": "provider_list_col", "component": { "Column": { "children": { "explicitList": ["provider_card_1", "provider_card_2"] } } } },
          { "id": "provider_card_1", "component": { "Card": { "child": "p1_col" } } },
          { "id": "p1_col", "component": { "Column": { "children": { "explicitList": ["p1_name", "p1_specialty", "p1_network", "p1_btn"] } } } },
          { "id": "p1_name", "component": { "Text": { "text": { "literalString": "Dr. Alice" }, "usageHint": "h2" } } },
          { "id": "p1_specialty", "component": { "Text": { "text": { "literalString": "Dermatology" } } } },
          { "id": "p1_network", "component": { "Text": { "text": { "literalString": "In-Network" } } } },
          { "id": "p1_btn", "component": { "Button": { "child": "p1_btn_txt", "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Check availability for Dr. Alice"}}, {"key": "provider_id", "value": {"literalString": "derma_1"}}] } } } },
          { "id": "p1_btn_txt", "component": { "Text": { "text": { "literalString": "Check Availability" } } } },
          
          { "id": "provider_card_2", "component": { "Card": { "child": "p2_col" } } },
          { "id": "p2_col", "component": { "Column": { "children": { "explicitList": ["p2_name", "p2_specialty", "p2_network", "p2_warning", "p2_btn"] } } } },
          { "id": "p2_name", "component": { "Text": { "text": { "literalString": "Dr. Charles" }, "usageHint": "h2" } } },
          { "id": "p2_specialty", "component": { "Text": { "text": { "literalString": "Dermatology" } } } },
          { "id": "p2_network", "component": { "Text": { "text": { "literalString": "Out-of-Network" } } } },
          { "id": "p2_warning", "component": { "Text": { "text": { "literalString": "Warning: Out-of-Network. Higher costs may apply." }, "usageHint": "warning" } } },
          { "id": "p2_btn", "component": { "Button": { "child": "p2_btn_txt", "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Check availability for Dr. Charles"}}, {"key": "provider_id", "value": {"literalString": "derma_3"}}] } } } },
          { "id": "p2_btn_txt", "component": { "Text": { "text": { "literalString": "Check Availability" } } } }
        ]
      }
    }
  ]
}
"""

AVAILABILITY_SELECTION_EXAMPLE = r"""
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "main", "root": "slots_col" } },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          { "id": "slots_col", "component": { "Column": { "children": { "explicitList": ["title_txt", "slot_btn_1", "slot_btn_2"] } } } },
          { "id": "title_txt", "component": { "Text": { "text": { "literalString": "Select a time slot:" }, "usageHint": "h3" } } },
          { "id": "slot_btn_1", "component": { "Button": { "child": "slot_txt_1", "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Book slot 2025-10-24 09:00"}}, {"key": "slot", "value": {"literalString": "2025-10-24 09:00"}}] } } } },
          { "id": "slot_txt_1", "component": { "Text": { "text": { "literalString": "09:00 AM" } } } },
          { "id": "slot_btn_2", "component": { "Button": { "child": "slot_txt_2", "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Book slot 2025-10-24 10:00"}}, {"key": "slot", "value": {"literalString": "2025-10-24 10:00"}}] } } } },
          { "id": "slot_txt_2", "component": { "Text": { "text": { "literalString": "10:00 AM" } } } }
        ]
      }
    }
  ]
}
"""

PROVIDER_SEARCH_FORM_EXAMPLE = r"""
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "main", "root": "search_form_col" } },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          { "id": "search_form_col", "component": { "Column": { "children": { "explicitList": ["title_txt", "specialty_mc", "zip_mc", "search_btn"] }, "distribution": "start", "alignment": "start" } } },
          { "id": "title_txt", "component": { "Text": { "text": { "literalString": "Find a Healthcare Provider" }, "usageHint": "h3" } } },
          { "id": "specialty_mc", "component": { "MultipleChoice": { "options": [
            { "label": { "literalString": "Dermatology" }, "value": "Dermatology" },
            { "label": { "literalString": "Primary Care" }, "value": "Primary Care" },
            { "label": { "literalString": "Pediatrics" }, "value": "Pediatrics" }
          ], "selections": { "path": "specialty" }, "maxAllowedSelections": 1 } } },
          { "id": "zip_mc", "component": { "MultipleChoice": { "options": [
            { "label": { "literalString": "30303" }, "value": "30303" },
            { "label": { "literalString": "30301" }, "value": "30301" },
            { "label": { "literalString": "30305" }, "value": "30305" },
            { "label": { "literalString": "30022" }, "value": "30022" },
            { "label": { "literalString": "30062" }, "value": "30062" }
          ], "selections": { "path": "zip_code" }, "maxAllowedSelections": 1 } } },
          { "id": "search_btn", "component": { "Button": { "child": "btn_txt", "primary": true, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Search for providers."}}, {"key": "specialty", "value": {"path": "specialty"}}, {"key": "zip_code", "value": {"path": "zip_code"}}] } } } },
          { "id": "btn_txt", "component": { "Text": { "text": { "literalString": "Search" } } } }
        ]
      }
    },
    { "dataModelUpdate": { "surfaceId": "main", "path": "/", "contents": [ { "key": "specialty", "valueString": "Primary Care" }, { "key": "zip_code", "valueString": "30303" } ] } }
  ]
}
"""

DATE_SELECTION_EXAMPLE = r"""
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "main", "root": "date_select_card" } },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          { "id": "date_select_card", "component": { "Card": { "child": "date_select_col" } } },
          { "id": "date_select_col", "component": { "Column": { "children": { "explicitList": ["title_txt", "date_input", "submit_btn"] } } } },
          { "id": "title_txt", "component": { "Text": { "text": { "literalString": "Select a date to check availability:" }, "usageHint": "h3" } } },
          { "id": "date_input", "component": { "DateTimeInput": { "value": {"path": "selected_date"}, "enableDate": true, "enableTime": false } } },
          { "id": "submit_btn", "component": { "Button": { "child": "btn_txt", "primary": true, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Check availability on selected date."}}, {"key": "date", "value": {"path": "selected_date"}}] } } } },
          { "id": "btn_txt", "component": { "Text": { "text": { "literalString": "Check Availability" } } } }
        ]
      }
    },
    { "dataModelUpdate": { "surfaceId": "main", "path": "/", "contents": [ { "key": "selected_date", "valueString": "2025-10-24" } ] } }
  ]
}
"""

BOOKING_CONFIRMATION_EXAMPLE = r"""
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "main", "root": "confirm_card" } },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          { "id": "confirm_card", "component": { "Card": { "child": "confirm_col" } } },
          { "id": "confirm_col", "component": { "Column": { "children": { "explicitList": ["title_txt", "provider_txt", "datetime_txt", "conf_id_txt"] } } } },
          { "id": "title_txt", "component": { "Text": { "text": { "literalString": "Appointment Confirmed!" }, "usageHint": "h2" } } },
          { "id": "provider_txt", "component": { "Text": { "text": { "literalString": "Provider: Dr. Alice" } } } },
          { "id": "datetime_txt", "component": { "Text": { "text": { "literalString": "Date/Time: 2025-10-24 09:00 AM" } } } },
          { "id": "conf_id_txt", "component": { "Text": { "text": { "literalString": "Confirmation ID: c8bec4e3" }, "usageHint": "caption" } } }
        ]
      }
    }
  ]
}
"""
