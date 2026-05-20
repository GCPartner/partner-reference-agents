PHONE_PLAN_SELECTION_EXAMPLES = r"""
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "main", "root": "root_card" } },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          { "id": "root_card", "component": { "Card": { "child": "card_col" } } },
          { "id": "card_col", "component": { "Column": { "children": { "explicitList": ["greeting_txt", "cb_plans", "cb_devices", "start_btn_row"] } } } },
          { "id": "greeting_txt", "component": { "Text": { "text": { "literalString": "Hi! I am the Phone Plan Concierge. What are you shopping for today?" }, "usageHint": "h2" } } },
          { "id": "cb_plans", "component": { "CheckBox": { "label": { "literalString": "Phone Plans" }, "value": {"path": "shop_plans"} } } },
          { "id": "cb_devices", "component": { "CheckBox": { "label": { "literalString": "Devices" }, "value": {"path": "shop_devices"} } } },
          { "id": "start_btn_row", "component": { "Row": { "children": { "explicitList": ["start_btn"] }, "distribution": "end" } } },
          { "id": "start_btn", "component": { "Button": { "child": "start_txt", "primary": true, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "I have selected what I am shopping for. Let's begin."}}, {"key": "shop_plans", "value": {"path": "shop_plans"}}, {"key": "shop_devices", "value": {"path": "shop_devices"}}] } } } },
          { "id": "start_txt", "component": { "Text": { "text": { "literalString": "Start Shopping" } } } }
        ]
      }
    },
    { "dataModelUpdate": { "surfaceId": "main", "path": "/", "contents": [ { "key": "shop_plans", "valueBoolean": true }, { "key": "shop_devices", "valueBoolean": true } ] } }
  ]
}
"""

NEEDS_ASSESSMENT_EXAMPLE = r"""
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "needs_assessment", "root": "form_col" } },
    {
      "surfaceUpdate": {
        "surfaceId": "needs_assessment",
        "components": [
          { "id": "form_col", "component": { "Column": { "children": { "explicitList": ["title_txt", "data_slider", "intl_cb", "budget_tf", "submit_btn"] }, "distribution": "start", "alignment": "start" } } },
          { "id": "title_txt", "component": { "Text": { "text": { "literalString": "Tell me about your phone plan needs." }, "usageHint": "h3" } } },
          { "id": "data_slider", "component": { "Slider": { "value": {"path": "data_gb"}, "minValue": 0, "maxValue": 100 } } },
          { "id": "intl_cb", "component": { "CheckBox": { "label": { "literalString": "Needs International Calling?" }, "value": {"path": "intl_calling"} } } },
          { "id": "budget_tf", "component": { "TextField": { "label": { "literalString": "Max Monthly Budget ($)" }, "text": {"path": "budget"}, "textFieldType": "shortText" } } },
          { "id": "submit_btn", "component": { "Button": { "child": "btn_txt", "primary": true, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "Find a match for my needs."}}, {"key": "data_gb", "value": {"path": "data_gb"}}, {"key": "intl_calling", "value": {"path": "intl_calling"}}, {"key": "budget", "value": {"path": "budget"}}] } } } },
          { "id": "btn_txt", "component": { "Text": { "text": { "literalString": "Find Match" } } } }
        ]
      }
    },
    { "dataModelUpdate": { "surfaceId": "needs_assessment", "path": "/", "contents": [ { "key": "data_gb", "valueNumber": 5 }, { "key": "intl_calling", "valueBoolean": false }, {"key": "budget", "valueString": ""} ] } }
  ]
}
"""

PLAN_SELECTION_EXAMPLE = r"""
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "plan_selection", "root": "plan_select_card" } },
    {
      "surfaceUpdate": {
        "surfaceId": "plan_selection",
        "components": [
          { "id": "plan_select_card", "component": { "Card": { "child": "plan_select_col" } } },
          { "id": "plan_select_col", "component": { "Column": { "children": { "explicitList": ["plan_title", "plan_list_col"] } } } },
          { "id": "plan_title", "component": { "Text": { "text": { "literalString": "Please select a plan:" }, "usageHint": "h3" } } },
          { "id": "plan_list_col", "component": { "Column": { "children": { "explicitList": ["plan_item_1", "plan_item_2"] } } } },
          
          { "id": "plan_item_1", "component": { "Card": { "child": "plan_row_1" } } },
          { "id": "plan_row_1", "component": { "Row": { "children": { "explicitList": ["plan_logo_1", "plan_details_1", "select_btn_1"] }, "alignment": "center" } } },
          { "id": "plan_logo_1", "component": { "Image": { "url": { "literalString": "https://upload.wikimedia.org/wikipedia/commons/5/5c/AT%26T-logo_2016.png" }, "usageHint": "avatar" } } },
          { "id": "plan_details_1", "component": { "Column": { "children": { "explicitList": ["plan_name_1", "plan_price_1"] } } } },
          { "id": "plan_name_1", "component": { "Text": { "text": { "literalString": "Global Traveler" }, "usageHint": "body" } } },
          { "id": "plan_price_1", "component": { "Text": { "text": { "literalString": "$75.00/mo" }, "usageHint": "caption" } } },
          { "id": "select_btn_1", "component": { "Button": { "child": "select_txt_1", "primary": true, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "I select the Global Traveler plan."}}, {"key": "selected_plan_id", "value": {"literalString": "p3"}}] } } } },
          { "id": "select_txt_1", "component": { "Text": { "text": { "literalString": "Select" } } } },

          { "id": "plan_item_2", "component": { "Card": { "child": "plan_row_2" } } },
          { "id": "plan_row_2", "component": { "Row": { "children": { "explicitList": ["plan_logo_2", "plan_details_2", "select_btn_2"] }, "alignment": "center" } } },
          { "id": "plan_logo_2", "component": { "Image": { "url": { "literalString": "https://example.com/verizon-logo.png" }, "usageHint": "avatar" } } },
          { "id": "plan_details_2", "component": { "Column": { "children": { "explicitList": ["plan_name_2", "plan_price_2"] } } } },
          { "id": "plan_name_2", "component": { "Text": { "text": { "literalString": "Premium International" }, "usageHint": "body" } } },
          { "id": "plan_price_2", "component": { "Text": { "text": { "literalString": "$85.00/mo" }, "usageHint": "caption" } } },
          { "id": "select_btn_2", "component": { "Button": { "child": "select_txt_2", "primary": true, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "I select the Premium International plan."}}, {"key": "selected_plan_id", "value": {"literalString": "p6"}}] } } } },
          { "id": "select_txt_2", "component": { "Text": { "text": { "literalString": "Select" } } } }
        ]
      }
    }
  ]
}
"""

DEVICE_SELECTION_EXAMPLE = r"""
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "device_selection", "root": "device_select_card" } },
    {
      "surfaceUpdate": {
        "surfaceId": "device_selection",
        "components": [
          { "id": "device_select_card", "component": { "Card": { "child": "device_select_col" } } },
          { "id": "device_select_col", "component": { "Column": { "children": { "explicitList": ["device_title", "device_list_col"] } } } },
          { "id": "device_title", "component": { "Text": { "text": { "literalString": "Please select a device:" }, "usageHint": "h3" } } },
          { "id": "device_list_col", "component": { "Column": { "children": { "explicitList": ["device_item_1", "device_item_2"] } } } },
          
          { "id": "device_item_1", "component": { "Card": { "child": "device_row_1" } } },
          { "id": "device_row_1", "component": { "Row": { "children": { "explicitList": ["device_img_1", "device_details_1", "select_btn_1"] }, "alignment": "center" } } },
          { "id": "device_img_1", "component": { "Image": { "url": { "literalString": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Google_Pixel_9_%28Wintergreen%29_rear.svg/500px-Google_Pixel_9_%28Wintergreen%29_rear.svg.png" }, "usageHint": "avatar" } } },
          { "id": "device_details_1", "component": { "Column": { "children": { "explicitList": ["device_name_1", "device_price_1"] } } } },
          { "id": "device_name_1", "component": { "Text": { "text": { "literalString": "Google Pixel 9" }, "usageHint": "body" } } },
          { "id": "device_price_1", "component": { "Text": { "text": { "literalString": "$799.00" }, "usageHint": "caption" } } },
          { "id": "select_btn_1", "component": { "Button": { "child": "select_txt_1", "primary": true, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "I select the Google Pixel 9."}}, {"key": "selected_device_id", "value": {"literalString": "d1"}}] } } } },
          { "id": "select_txt_1", "component": { "Text": { "text": { "literalString": "Select" } } } },

          { "id": "device_item_2", "component": { "Card": { "child": "device_row_2" } } },
          { "id": "device_row_2", "component": { "Row": { "children": { "explicitList": ["device_img_2", "device_details_2", "select_btn_2"] }, "alignment": "center" } } },
          { "id": "device_img_2", "component": { "Image": { "url": { "literalString": "https://example.com/iphone15.png" }, "usageHint": "avatar" } } },
          { "id": "device_details_2", "component": { "Column": { "children": { "explicitList": ["device_name_2", "device_price_2"] } } } },
          { "id": "device_name_2", "component": { "Text": { "text": { "literalString": "Apple iPhone 15" }, "usageHint": "body" } } },
          { "id": "device_price_2", "component": { "Text": { "text": { "literalString": "$799.00" }, "usageHint": "caption" } } },
          { "id": "select_btn_2", "component": { "Button": { "child": "select_txt_2", "primary": true, "action": { "name": "submit", "context": [{"key": "message", "value": {"literalString": "I select the Apple iPhone 15."}}, {"key": "selected_device_id", "value": {"literalString": "d3"}}] } } } },
          { "id": "select_txt_2", "component": { "Text": { "text": { "literalString": "Select" } } } }
        ]
      }
    }
  ]
}
"""
