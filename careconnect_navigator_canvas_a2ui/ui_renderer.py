import json

# ----------------------------------------------------------------------
# A2UI envelope formatter
# ----------------------------------------------------------------------
def _wrap_envelope(messages: list) -> str:
    payload = {"messages": messages}
    return f"\n---a2ui_JSON---\n{json.dumps(payload, indent=2)}"


# ----------------------------------------------------------------------
# Step 1: Plan Selection Form
# ----------------------------------------------------------------------
def render_plan_selection(selected_plan: str = None) -> str:
    messages = [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": "navigator",
                "catalogId": "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json",
                "theme": { "primaryColor": "#0D9488" }
            }
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "navigator",
                "components": [
                    { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "medical_services" },
                    { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
                    { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "title_txt", "plan_mc", "footer_row"], "align": "stretch" },
                    
                    { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
                    { "id": "step_icon", "component": "MaterialIcon", "icon": "assignment", "color": "primary" },
                    { "id": "step_txt", "component": "MaterialText", "text": "**Step 1 of 5: Select Plan**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
                    
                    { "id": "title_txt", "component": "MaterialText", "text": "Please choose your insurance plan type:", "usageHint": "h3", "style": { "color": "#0F766E", "marginBottom": "15px" } },
                    { "id": "plan_mc", "component": "ChoicePicker", "variant": "mutuallyExclusive", "options": [
                        { "label": "HMO Plan", "value": "HMO" },
                        { "label": "PPO Plan", "value": "PPO" }
                    ], "value": { "path": "/plan_type" } },
                    
                    { "id": "footer_row", "component": "MaterialRow", "children": ["back_btn", "next_btn"], "justify": "space-between", "style": { "marginTop": "20px" } },
                    { "id": "back_btn", "component": "MaterialButton", "label": "Cancel", "variant": "stroked", "disabled": True },
                    { "id": "next_btn", "component": "MaterialButton", "label": "Next", "variant": "raised", "trailingIcon": "arrow_forward", "action": { "event": { "name": "submit", "context": {"message": "Selected plan type", "current_step": 1, "plan_type": {"path": "/plan_type"}} } }, "style": { "backgroundColor": "#0D9488", "color": "white" } }
                ]
            }
        },
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": "navigator",
                "path": "/",
                "value": { "plan_type": selected_plan or "", "current_step": 1 }
            }
        }
    ]
    return _wrap_envelope(messages)


# ----------------------------------------------------------------------
# Step 2: Search Criteria Form
# ----------------------------------------------------------------------
def render_search_criteria(plan_type: str, specialty: str = None, zip_code: str = None) -> str:
    messages = [
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "navigator",
                "components": [
                    { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "search" },
                    { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
                    { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "title_txt", "spec_mc", "zip_mc", "footer_row"], "align": "stretch" },
                    
                    { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
                    { "id": "step_icon", "component": "MaterialIcon", "icon": "search", "color": "primary" },
                    { "id": "step_txt", "component": "MaterialText", "text": f"**Step 2 of 5: Search ({plan_type})**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
                    
                    { "id": "title_txt", "component": "MaterialText", "text": "Select specialty and zip code:", "usageHint": "h3", "style": { "color": "#0F766E", "marginBottom": "15px" } },
                    { "id": "spec_mc", "component": "MaterialSelect", "label": "Specialty", "options": [
                        { "label": "Dermatology", "value": "Dermatology" },
                        { "label": "Physical Therapy", "value": "Physical Therapy" },
                        { "label": "Pediatrics", "value": "Pediatrics" },
                        { "label": "Primary Care", "value": "Primary Care" },
                        { "label": "Cardiology", "value": "Cardiology" }
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
                "value": { "plan_type": plan_type, "specialty": specialty or "", "zip_code": zip_code or "", "current_step": 2 }
            }
        }
    ]
    return _wrap_envelope(messages)


# ----------------------------------------------------------------------
# Step 3: Provider Selection Card List
# ----------------------------------------------------------------------
def render_provider_list(providers: list, specialty: str, zip_code: str, plan_type: str) -> str:
    components = [
        { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "medical_services" },
        { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
        { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "title_txt", "provider_list_col", "footer_row"], "align": "stretch" },
        
        { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
        { "id": "step_icon", "component": "MaterialIcon", "icon": "medical_services", "color": "primary" },
        { "id": "step_txt", "component": "MaterialText", "text": "**Step 3 of 5: Select Provider**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
        
        { "id": "title_txt", "component": "MaterialText", "text": f"Found {len(providers)} providers for your search:", "usageHint": "h3", "style": { "color": "#0F766E", "marginBottom": "10px" } },
        { "id": "provider_list_col", "component": "MaterialColumn", "children": [f"{p['id']}_card" for p in providers], "align": "stretch" }
    ]
    
    # Dynamically generate elements for each provider card
    for p in providers:
        card_id = f"{p['id']}_card"
        row_id = f"{p['id']}_row"
        img_id = f"{p['id']}_img"
        col_id = f"{p['id']}_col"
        name_id = f"{p['id']}_name"
        net_id = f"{p['id']}_net"
        btn_id = f"{p['id']}_btn"
        
        is_oon = "OON" in p.get("networks", [])
        card_color = "#FFFFFF"
        border_color = "#CCFBF1" if not is_oon else "#FCA5A5"
        
        card_children = [row_id]
        row_children = [img_id, col_id]
        
        # Details column children
        col_children = [name_id, net_id]
        
        if is_oon:
            warn_row_id = f"{p['id']}_warn"
            warn_icon_id = f"{p['id']}_warn_icon"
            warn_txt_id = f"{p['id']}_warn_txt"
            col_children.append(warn_row_id)
            
            components.extend([
                { "id": warn_row_id, "component": "MaterialRow", "children": [warn_icon_id, warn_txt_id], "align": "center", "style": { "backgroundColor": "#FEE2E2", "padding": "6px", "borderRadius": "4px", "marginBottom": "8px" } },
                { "id": warn_icon_id, "component": "MaterialIcon", "icon": "warning", "color": "warn" },
                { "id": warn_txt_id, "component": "MaterialText", "text": "Out-of-Network. Higher costs may apply.", "usageHint": "caption", "style": { "color": "#B91C1C", "marginLeft": "5px" } }
            ])
            
        col_children.append(btn_id)
        
        # Append main card components
        components.extend([
            { "id": card_id, "component": "MaterialCard", "appearance": "outlined", "children": card_children, "style": { "backgroundColor": card_color, "border": f"1px solid {border_color}", "borderRadius": "8px", "padding": "12px", "marginBottom": "10px" } },
            { "id": row_id, "component": "MaterialRow", "children": row_children, "align": "center" },
            { "id": img_id, "component": "Image", "url": p.get("photo_url", ""), "description": p["name"], "variant": "smallFeature", "fit": "cover" },
            { "id": col_id, "component": "MaterialColumn", "children": col_children, "align": "stretch" },
            { "id": name_id, "component": "MaterialText", "text": p["name"], "usageHint": "h3", "style": { "color": "#0F766E" if not is_oon else "#B91C1C" } },
            { "id": net_id, "component": "MaterialText", "text": f"Specialty: {p['specialty']} | Zip: {p['zip']}", "usageHint": "body" },
            { "id": btn_id, "component": "MaterialButton", "label": "Select " + p["name"].split(" ")[0] + " " + p["name"].split(" ")[1], "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": f"Selected provider {p['name']}", "current_step": 3, "selected_provider_id": p["id"]} } }, "style": { "backgroundColor": "#0D9488" if not is_oon else "#DC2626", "color": "white" } }
        ])
        
    # Append common footer navigation components
    components.extend([
        { "id": "footer_row", "component": "MaterialRow", "children": ["back_btn", "next_btn"], "justify": "space-between", "style": { "marginTop": "20px" } },
        { "id": "back_btn", "component": "MaterialButton", "label": "Back", "variant": "stroked", "leadingIcon": "arrow_back", "action": { "event": { "name": "submit", "context": {"message": "Go Back to Step 2", "current_step": 3, "direction": "back"} } } },
        { "id": "next_btn", "component": "MaterialButton", "label": "Next", "variant": "raised", "disabled": True }
    ])
    
    messages = [
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "navigator",
                "components": components
            }
        },
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": "navigator",
                "path": "/",
                "value": { "plan_type": plan_type, "specialty": specialty, "zip_code": zip_code, "selected_provider_id": "", "current_step": 3 }
            }
        }
    ]
    return _wrap_envelope(messages)


# ----------------------------------------------------------------------
# Step 4 Part A: Date Selection Picker
# ----------------------------------------------------------------------
def render_date_picker(provider_id: str, plan_type: str, selected_date: str = "2025-10-24") -> str:
    messages = [
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
                "value": { "selected_provider_id": provider_id, "plan_type": plan_type, "selected_date": selected_date, "current_step": 4 }
            }
        }
    ]
    return _wrap_envelope(messages)


# ----------------------------------------------------------------------
# Step 4 Part B: Available Slots Grid Picker
# ----------------------------------------------------------------------
def render_availability_grid(slots: list, provider_id: str, plan_type: str, selected_date: str) -> str:
    components = [
        { "id": "root", "component": "Canvas", "children": ["canvas_card"], "cardTitle": "CareConnect Navigator", "cardDescription": "Appointment booking wizard", "cardIcon": "schedule" },
        { "id": "canvas_card", "component": "MaterialCard", "appearance": "raised", "children": ["canvas_col"], "style": { "backgroundColor": "#F0FDFA", "border": "1px solid #E6F4F1", "borderRadius": "8px", "padding": "20px" } },
        { "id": "canvas_col", "component": "MaterialColumn", "children": ["header_row", "title_txt", "slots_grid", "footer_row"], "align": "stretch" },
        
        { "id": "header_row", "component": "MaterialRow", "children": ["step_icon", "step_txt"], "align": "center", "style": { "marginBottom": "15px" } },
        { "id": "step_icon", "component": "MaterialIcon", "icon": "schedule", "color": "primary" },
        { "id": "step_txt", "component": "MaterialText", "text": f"**Step 4 of 5: Available Slots ({selected_date})**", "usageHint": "h3", "style": { "color": "#0F766E", "marginLeft": "10px" } },
        
        { "id": "title_txt", "component": "MaterialText", "text": "Choose an available time slot below:", "usageHint": "h3", "style": { "color": "#0F766E", "marginBottom": "15px" } }
    ]
    
    # Determine the children buttons of the grid (maximum 4 buttons/row logic)
    grid_children = []
    for i, s in enumerate(slots):
        btn_id = f"slot_btn_{i}"
        grid_children.append(btn_id)
        
        components.append({
            "id": btn_id,
            "component": "MaterialButton",
            "label": s,
            "variant": "raised",
            "action": {
                "event": {
                    "name": "submit",
                    "context": {
                        "message": f"Selected time slot {s}",
                        "current_step": 4,
                        "selected_slot": s
                    }
                }
            },
            "style": { "backgroundColor": "#0D9488", "color": "white", "marginBottom": "10px" }
        })
        
    # Append the slots grid wrapper
    components.append({
        "id": "slots_grid",
        "component": "MaterialColumn",
        "children": grid_children,
        "align": "stretch"
    })
    
    # Add footer navigation
    components.extend([
        { "id": "footer_row", "component": "MaterialRow", "children": ["back_btn", "next_btn"], "justify": "space-between", "style": { "marginTop": "20px" } },
        { "id": "back_btn", "component": "MaterialButton", "label": "Back", "variant": "stroked", "leadingIcon": "arrow_back", "action": { "event": { "name": "submit", "context": {"message": "Change Date selection", "current_step": 4, "direction": "back_to_date"} } } },
        { "id": "next_btn", "component": "MaterialButton", "label": "Next", "variant": "raised", "disabled": True }
    ])
    
    messages = [
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "navigator",
                "components": components
            }
        },
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": "navigator",
                "path": "/",
                "value": { "selected_provider_id": provider_id, "plan_type": plan_type, "selected_date": selected_date, "selected_slot": "", "current_step": 4 }
            }
        }
    ]
    return _wrap_envelope(messages)


# ----------------------------------------------------------------------
# Step 5: Review appointment & booking trigger screen
# ----------------------------------------------------------------------
def render_review_screen(plan_type: str, provider_name: str, photo_url: str, selected_slot: str) -> str:
    messages = [
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
                    { "id": "summary_img", "component": "Image", "url": photo_url, "description": provider_name, "variant": "smallFeature", "fit": "cover" },
                    { "id": "summary_col", "component": "MaterialColumn", "children": ["plan_txt", "provider_txt", "datetime_txt"], "align": "stretch" },
                    { "id": "plan_txt", "component": "MaterialText", "text": f"Insurance Plan: {plan_type}", "usageHint": "body" },
                    { "id": "provider_txt", "component": "MaterialText", "text": f"Provider: {provider_name}", "usageHint": "body" },
                    { "id": "datetime_txt", "component": "MaterialText", "text": f"Selected Time: {selected_slot}", "usageHint": "body" },
                    
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
    return _wrap_envelope(messages)


# ----------------------------------------------------------------------
# Step 6: Confirmation Screen
# ----------------------------------------------------------------------
def render_confirmation_screen(provider_name: str, selected_slot: str, confirmation_id: str) -> str:
    messages = [
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
                    { "id": "provider_txt", "component": "MaterialText", "text": f"Provider: {provider_name}", "usageHint": "body" },
                    { "id": "datetime_txt", "component": "MaterialText", "text": f"Date/Time: {selected_slot}", "usageHint": "body" },
                    { "id": "conf_id_txt", "component": "MaterialText", "text": f"Confirmation ID: {confirmation_id}", "usageHint": "caption", "style": { "fontWeight": "bold", "color": "#0D9488", "marginTop": "5px" } },
                    
                    { "id": "footer_row", "component": "MaterialRow", "children": ["start_btn"], "justify": "center", "style": { "marginTop": "20px" } },
                    { "id": "start_btn", "component": "MaterialButton", "label": "Book Another Appointment", "variant": "raised", "action": { "event": { "name": "submit", "context": {"message": "Restart the booking wizard to search again", "current_step": 6, "direction": "restart"} } }, "style": { "backgroundColor": "#0D9488", "color": "white" } }
                ]
            }
        }
    ]
    return _wrap_envelope(messages)
