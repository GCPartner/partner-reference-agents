# CareConnect Navigator Canvas A2UI Examples (v0.9)
# All examples are redesigned to use a single persistent surface: "navigator"

PLAN_CLARIFICATION_EXAMPLE = r"""
{
  "messages": [
    {
      "version": "v0.9",
      "updateComponents": {
        "surfaceId": "navigator",
        "components": [
          { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "health_and_safety" },
          { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
          { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "title_txt", "plan_mc", "footer_row"], "align": "stretch" },
          
          { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
          { "id": "step_icon", "component": "MaterialIcon", "icon": "health_and_safety", "color": "primary" },
          { "id": "step_txt", "component": "MaterialText", "text": "**Step 1 of 5: Insurance Plan**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
          
          { "id": "title_txt", "component": "MaterialText", "text": "Please select your plan type:", "usageHint": "h3", "style": { "color": "#0F766E", "marginBottom": "10px" } },
          { "id": "plan_mc", "component": "MaterialRadioButton", "options": [
            { "label": "HMO (Requires referral)", "value": "HMO" },
            { "label": "PPO (More flexible)", "value": "PPO" }
          ], "value": { "path": "/plan_type" }, "color": "primary" },
          
          { "id": "footer_row", "component": "MaterialRow", "children": ["back_btn", "next_btn"], "justify": "space-between", "style": { "marginTop": "20px" } },
          { "id": "back_btn", "component": "MaterialButton", "label": "Back", "variant": "stroked", "disabled": true },
          { "id": "next_btn", "component": "MaterialButton", "label": "Next", "variant": "raised", "trailingIcon": "arrow_forward", "action": { "event": { "name": "submit", "context": {"message": "Go to Step 2", "current_step": 1, "plan_type": {"path": "/plan_type"}} } }, "style": { "backgroundColor": "#0D9488", "color": "white" } }
        ]
      }
    },
    {
      "version": "v0.9",
      "updateDataModel": {
        "surfaceId": "navigator",
        "path": "/",
        "value": { "plan_type": "HMO", "current_step": 1 }
      }
    }
  ]
}
"""

PROVIDER_SEARCH_FORM_EXAMPLE = r"""
{
  "messages": [
    {
      "version": "v0.9",
      "updateComponents": {
        "surfaceId": "navigator",
        "components": [
          { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "search" },
          { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
          { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "title_txt", "form_col", "footer_row"], "align": "stretch" },
          
          { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
          { "id": "step_icon", "component": "MaterialIcon", "icon": "search", "color": "primary" },
          { "id": "step_txt", "component": "MaterialText", "text": "**Step 2 of 5: Search Criteria**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
          
          { "id": "title_txt", "component": "MaterialText", "text": "What type of specialist do you need and in which zip code?", "usageHint": "h3", "style": { "color": "#0F766E", "marginBottom": "10px" } },
          
          { "id": "form_col", "component": "MaterialColumn", "children": ["specialty_mc", "zip_mc"], "align": "stretch" },
          { "id": "specialty_mc", "component": "MaterialSelect", "label": "Specialty", "options": [
            { "label": "Physical Therapy", "value": "Physical Therapy" },
            { "label": "Dermatology", "value": "Dermatology" },
            { "label": "Cardiology", "value": "Cardiology" },
            { "label": "Pediatrics", "value": "Pediatrics" },
            { "label": "Primary Care", "value": "Primary Care" }
          ], "value": { "path": "/specialty" } },
          { "id": "zip_mc", "component": "MaterialSelect", "label": "Zip Code", "options": [
            { "label": "30303", "value": "30303" },
            { "label": "30301", "value": "30301" },
            { "label": "30305", "value": "30305" },
            { "label": "30022", "value": "30022" },
            { "label": "30062", "value": "30062" }
          ], "value": { "path": "/zip_code" } },
          
          { "id": "footer_row", "component": "MaterialRow", "children": ["back_btn", "next_btn"], "justify": "space-between", "style": { "marginTop": "20px" } },
          { "id": "back_btn", "component": "MaterialButton", "label": "Back", "variant": "stroked", "leadingIcon": "arrow_back", "action": { "event": { "name": "submit", "context": {"message": "Go Back to Step 1", "current_step": 2, "direction": "back"} } } },
          { "id": "next_btn", "component": "MaterialButton", "label": "Next", "variant": "raised", "trailingIcon": "arrow_forward", "action": { "event": { "name": "submit", "context": {"message": "Search for providers", "current_step": 2, "specialty": {"path": "/specialty"}, "zip_code": {"path": "/zip_code"}} } }, "style": { "backgroundColor": "#0D9488", "color": "white" } }
        ]
      }
    },
    {
      "version": "v0.9",
      "updateDataModel": {
        "surfaceId": "navigator",
        "path": "/",
        "value": { "specialty": "Physical Therapy", "zip_code": "30303", "current_step": 2 }
      }
    }
  ]
}
"""

PROVIDER_LIST_EXAMPLE = r"""
{
  "messages": [
    {
      "version": "v0.9",
      "updateComponents": {
        "surfaceId": "navigator",
        "components": [
          { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "medical_services" },
          { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
          { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "title_txt", "provider_list_col", "footer_row"], "align": "stretch" },
          
          { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
          { "id": "step_icon", "component": "MaterialIcon", "icon": "medical_services", "color": "primary" },
          { "id": "step_txt", "component": "MaterialText", "text": "**Step 3 of 5: Select Provider**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
          
          { "id": "title_txt", "component": "MaterialText", "text": "Select a provider below:", "usageHint": "h3", "style": { "color": "#0F766E", "marginBottom": "10px" } },
          
          { "id": "provider_list_col", "component": "MaterialColumn", "children": ["p1_card", "p2_card"], "align": "stretch" },
          
          { "id": "p1_card", "component": "MaterialCard", "appearance": "outlined", "children": ["p1_row"], "style": { "backgroundColor": "#FFFFFF", "border": "1px solid #CCFBF1", "borderRadius": "8px", "padding": "12px", "marginBottom": "10px" } },
          { "id": "p1_row", "component": "MaterialRow", "children": ["p1_img", "p1_col"], "align": "center" },
          { "id": "p1_img", "component": "Image", "url": "https://storage.googleapis.com/careconnect-nav-canvas-assets-agentspace-demo-1145-b/doctor_alice_v2.jpg", "description": "Dr. Alice", "variant": "avatar", "fit": "cover" },
          { "id": "p1_col", "component": "MaterialColumn", "children": ["p1_name", "p1_net", "p1_btn"], "align": "stretch" },
          { "id": "p1_name", "component": "MaterialText", "text": "Dr. Alice (In-Network)", "usageHint": "h3", "style": { "color": "#0F766E" } },
          { "id": "p1_net", "component": "MaterialText", "text": "Specialty: Physical Therapy | Zip: 30303", "usageHint": "body" },
          { "id": "p1_btn", "component": "MaterialButton", "label": "Select Dr. Alice", "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": "Selected provider Dr. Alice", "current_step": 3, "selected_provider_id": "pt_30303_1"} } }, "style": { "backgroundColor": "#0D9488", "color": "white" } },
          
          { "id": "p2_card", "component": "MaterialCard", "appearance": "outlined", "children": ["p2_row"], "style": { "backgroundColor": "#FFFFFF", "border": "1px solid #FCA5A5", "borderRadius": "8px", "padding": "12px", "marginBottom": "10px" } },
          { "id": "p2_row", "component": "MaterialRow", "children": ["p2_img", "p2_col"], "align": "center" },
          { "id": "p2_img", "component": "Image", "url": "https://storage.googleapis.com/careconnect-nav-canvas-assets-agentspace-demo-1145-b/doctor_charles_v2.jpg", "description": "Dr. Charles", "variant": "avatar", "fit": "cover" },
          { "id": "p2_col", "component": "MaterialColumn", "children": ["p2_name", "p2_net", "p2_warn", "p2_btn"], "align": "stretch" },
          { "id": "p2_name", "component": "MaterialText", "text": "Dr. Charles (Out-of-Network)", "usageHint": "h3", "style": { "color": "#B91C1C" } },
          { "id": "p2_net", "component": "MaterialText", "text": "Specialty: Physical Therapy | Zip: 30303", "usageHint": "body" },
          { "id": "p2_warn", "component": "MaterialRow", "children": ["warn_icon", "warn_txt"], "align": "center", "style": { "backgroundColor": "#FEE2E2", "padding": "6px", "borderRadius": "4px", "marginBottom": "8px" } },
          { "id": "warn_icon", "component": "MaterialIcon", "icon": "warning", "color": "warn" },
          { "id": "warn_txt", "component": "MaterialText", "text": "Out-of-Network. Higher costs may apply.", "usageHint": "caption", "style": { "color": "#B91C1C", "marginLeft": "5px" } },
          { "id": "p2_btn", "component": "MaterialButton", "label": "Select Dr. Charles", "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": "Selected provider Dr. Charles", "current_step": 3, "selected_provider_id": "pt_30303_3"} } }, "style": { "backgroundColor": "#DC2626", "color": "white" } },
          
          { "id": "footer_row", "component": "MaterialRow", "children": ["back_btn", "next_btn"], "justify": "space-between", "style": { "marginTop": "20px" } },
          { "id": "back_btn", "component": "MaterialButton", "label": "Back", "variant": "stroked", "leadingIcon": "arrow_back", "action": { "event": { "name": "submit", "context": {"message": "Go Back to Step 2", "current_step": 3, "direction": "back"} } } },
          { "id": "next_btn", "component": "MaterialButton", "label": "Next", "variant": "raised", "disabled": true }
        ]
      }
    },
    {
      "version": "v0.9",
      "updateDataModel": {
        "surfaceId": "navigator",
        "path": "/",
        "value": { "selected_provider_id": "", "current_step": 3 }
      }
    }
}
"""

DATE_SELECTION_EXAMPLE = r"""
{
  "messages": [
    {
      "version": "v0.9",
      "updateComponents": {
        "surfaceId": "navigator",
        "components": [
          { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "event" },
          { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
          { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "title_txt", "date_input", "footer_row"], "align": "stretch" },
          
          { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
          { "id": "step_icon", "component": "MaterialIcon", "icon": "event", "color": "primary" },
          { "id": "step_txt", "component": "MaterialText", "text": "**Step 4 of 5: Appointment Date**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
          
          { "id": "title_txt", "component": "MaterialText", "text": "Select a date to check availability:", "usageHint": "h3", "style": { "color": "#0F766E", "marginBottom": "15px" } },
          { "id": "date_input", "component": "MaterialDatepicker", "label": "Choose Date", "value": {"path": "/selected_date"} },
          
          { "id": "footer_row", "component": "MaterialRow", "children": ["back_btn", "next_btn"], "justify": "space-between", "style": { "marginTop": "20px" } },
          { "id": "back_btn", "component": "MaterialButton", "label": "Back", "variant": "stroked", "leadingIcon": "arrow_back", "action": { "event": { "name": "submit", "context": {"message": "Go Back to Step 3", "current_step": 4, "direction": "back"} } } },
          { "id": "next_btn", "component": "MaterialButton", "label": "Next", "variant": "raised", "trailingIcon": "arrow_forward", "action": { "event": { "name": "submit", "context": {"message": "Check availability on selected date", "current_step": 4, "selected_date": {"path": "/selected_date"}} } }, "style": { "backgroundColor": "#0D9488", "color": "white" } }
        ]
      }
    },
    {
      "version": "v0.9",
      "updateDataModel": {
        "surfaceId": "navigator",
        "path": "/",
        "value": { "selected_date": { "year": 2025, "month": 10, "day": 24 }, "current_step": 4 }
      }
    }
  ]
}
"""

AVAILABILITY_SELECTION_EXAMPLE = r"""
{
  "messages": [
    {
      "version": "v0.9",
      "updateComponents": {
        "surfaceId": "navigator",
        "components": [
          { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "event" },
          { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
          { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "title_txt", "slots_row_1", "slots_row_2", "footer_row"], "align": "stretch" },
          
          { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
          { "id": "step_icon", "component": "MaterialIcon", "icon": "event", "color": "primary" },
          { "id": "step_txt", "component": "MaterialText", "text": "**Step 4 of 5: Select Time Slot**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
          
          { "id": "title_txt", "component": "MaterialText", "text": "Select an available slot:", "usageHint": "h3", "style": { "color": "#0F766E", "marginBottom": "15px" } },
          
          { "id": "slots_row_1", "component": "MaterialRow", "children": ["slot_btn_1", "slot_btn_2", "slot_btn_3"], "justify": "start", "style": { "marginBottom": "10px" } },
          { "id": "slot_btn_1", "component": "MaterialButton", "label": "09:00 AM", "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": "Selected slot 2025-10-24 09:00", "current_step": 4, "selected_slot": "2025-10-24 09:00"} } }, "style": { "backgroundColor": "#E6F4F1", "color": "#0F766E", "border": "1px solid #0D9488", "marginRight": "10px" } },
          { "id": "slot_btn_2", "component": "MaterialButton", "label": "10:00 AM", "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": "Selected slot 2025-10-24 10:00", "current_step": 4, "selected_slot": "2025-10-24 10:00"} } }, "style": { "backgroundColor": "#E6F4F1", "color": "#0F766E", "border": "1px solid #0D9488", "marginRight": "10px" } },
          { "id": "slot_btn_3", "component": "MaterialButton", "label": "11:00 AM", "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": "Selected slot 2025-10-24 11:00", "current_step": 4, "selected_slot": "2025-10-24 11:00"} } }, "style": { "backgroundColor": "#E6F4F1", "color": "#0F766E", "border": "1px solid #0D9488" } },
          
          { "id": "slots_row_2", "component": "MaterialRow", "children": ["slot_btn_4", "slot_btn_5", "slot_btn_6"], "justify": "start" },
          { "id": "slot_btn_4", "component": "MaterialButton", "label": "01:00 PM", "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": "Selected slot 2025-10-24 13:00", "current_step": 4, "selected_slot": "2025-10-24 13:00"} } }, "style": { "backgroundColor": "#E6F4F1", "color": "#0F766E", "border": "1px solid #0D9488", "marginRight": "10px" } },
          { "id": "slot_btn_5", "component": "MaterialButton", "label": "02:00 PM", "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": "Selected slot 2025-10-24 14:00", "current_step": 4, "selected_slot": "2025-10-24 14:00"} } }, "style": { "backgroundColor": "#E6F4F1", "color": "#0F766E", "border": "1px solid #0D9488", "marginRight": "10px" } },
          { "id": "slot_btn_6", "component": "MaterialButton", "label": "03:00 PM", "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": "Selected slot 2025-10-24 15:00", "current_step": 4, "selected_slot": "2025-10-24 15:00"} } }, "style": { "backgroundColor": "#E6F4F1", "color": "#0F766E", "border": "1px solid #0D9488" } },
          
          { "id": "footer_row", "component": "MaterialRow", "children": ["back_btn", "next_btn"], "justify": "space-between", "style": { "marginTop": "20px" } },
          { "id": "back_btn", "component": "MaterialButton", "label": "Back", "variant": "stroked", "leadingIcon": "arrow_back", "action": { "event": { "name": "submit", "context": {"message": "Go Back to Step 3", "current_step": 4, "direction": "back"} } } },
          { "id": "next_btn", "component": "MaterialButton", "label": "Next", "variant": "raised", "disabled": true }
        ]
      }
    },
    {
      "version": "v0.9",
      "updateDataModel": {
        "surfaceId": "navigator",
        "path": "/",
        "value": { "selected_slot": "", "current_step": 4 }
      }
    }
  ]
}
"""

BOOKING_CONFIRMATION_EXAMPLE = r"""
{
  "messages": [
    {
      "version": "v0.9",
      "updateComponents": {
        "surfaceId": "navigator",
        "components": [
          { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "check_circle" },
          { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
          { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "confirm_card", "footer_row"], "align": "stretch" },
          
          { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
          { "id": "step_icon", "component": "MaterialIcon", "icon": "check_circle", "color": "primary" },
          { "id": "step_txt", "component": "MaterialText", "text": "**Booking Confirmed!**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
          
          { "id": "confirm_card", "component": "MaterialCard", "appearance": "outlined", "children": ["confirm_col"], "style": { "backgroundColor": "#FFFFFF", "border": "1px solid #CCFBF1", "borderRadius": "8px", "padding": "15px" } },
          { "id": "confirm_col", "component": "MaterialColumn", "children": ["title_txt", "provider_txt", "datetime_txt", "conf_id_txt"], "align": "stretch" },
          { "id": "title_txt", "component": "MaterialText", "text": "Appointment Scheduled Successfully", "usageHint": "h2", "style": { "color": "#0F766E" } },
          { "id": "provider_txt", "component": "MaterialText", "text": "Provider: Dr. Alice", "usageHint": "body" },
          { "id": "datetime_txt", "component": "MaterialText", "text": "Date/Time: 2025-10-24 09:00 AM", "usageHint": "body" },
          { "id": "conf_id_txt", "component": "MaterialText", "text": "Confirmation ID: c8bec4e3", "usageHint": "caption", "style": { "fontWeight": "bold", "color": "#0D9488", "marginTop": "5px" } },
          
          { "id": "footer_row", "component": "MaterialRow", "children": ["start_btn"], "justify": "center", "style": { "marginTop": "20px" } },
          { "id": "start_btn", "component": "MaterialButton", "label": "Book Another Appointment", "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": "Restart the booking wizard to search again", "current_step": 6, "direction": "restart"} } }, "style": { "backgroundColor": "#0D9488", "color": "white" } }
        ]
      }
    }
  ]
}
"""

REVIEW_AND_BOOK_EXAMPLE = r"""
{
  "messages": [
    {
      "version": "v0.9",
      "updateComponents": {
        "surfaceId": "navigator",
        "components": [
          { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "rate_review" },
          { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
          { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "title_txt", "summary_card", "footer_row"], "align": "stretch" },
          
          { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
          { "id": "step_icon", "component": "MaterialIcon", "icon": "rate_review", "color": "primary" },
          { "id": "step_txt", "component": "MaterialText", "text": "**Step 5 of 5: Review & Confirm**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
          
          { "id": "title_txt", "component": "MaterialText", "text": "Please review your appointment details:", "usageHint": "h3", "style": { "color": "#0F766E", "marginBottom": "10px" } },
          
          { "id": "summary_card", "component": "MaterialCard", "appearance": "outlined", "children": ["summary_row"], "style": { "backgroundColor": "#FFFFFF", "border": "1px solid #CCFBF1", "borderRadius": "8px", "padding": "15px" } },
          { "id": "summary_row", "component": "MaterialRow", "children": ["summary_img", "summary_col"], "align": "center" },
          { "id": "summary_img", "component": "Image", "url": "https://storage.googleapis.com/careconnect-nav-canvas-assets-agentspace-demo-1145-b/doctor_alice_v2.jpg", "description": "Dr. Alice", "variant": "avatar", "fit": "cover" },
          { "id": "summary_col", "component": "MaterialColumn", "children": ["plan_txt", "provider_txt", "datetime_txt"], "align": "stretch" },
          { "id": "plan_txt", "component": "MaterialText", "text": "Insurance Plan: HMO", "usageHint": "body" },
          { "id": "provider_txt", "component": "MaterialText", "text": "Provider: Dr. Alice Physical Therapy (Zip 30303) (In-Network)", "usageHint": "body" },
          { "id": "datetime_txt", "component": "MaterialText", "text": "Selected Time: 2025-10-24 09:00", "usageHint": "body" },
          
          { "id": "footer_row", "component": "MaterialRow", "children": ["back_btn", "next_btn"], "justify": "space-between", "style": { "marginTop": "20px" } },
          { "id": "back_btn", "component": "MaterialButton", "label": "Back", "variant": "stroked", "leadingIcon": "arrow_back", "action": { "event": { "name": "submit", "context": {"message": "Go Back to Step 4", "current_step": 5, "direction": "back"} } } },
          { "id": "next_btn", "component": "MaterialButton", "label": "Book Appointment", "variant": "raised", "trailingIcon": "check", "action": { "event": { "name": "submit", "context": {"message": "Book the appointment", "current_step": 5, "book_action": "true"} } }, "style": { "backgroundColor": "#0D9488", "color": "white" } }
        ]
      }
    },
    {
      "version": "v0.9",
      "updateDataModel": {
        "surfaceId": "navigator",
        "path": "/",
        "value": { "current_step": 5 }
      }
    }
  ]
}
"""
