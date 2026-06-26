import json
from typing import List, Dict, Any

def get_discovery_ui(files: List[str]) -> str:
    """Generates the A2UI JSON payload for listing quarantined files."""
    components = [
        {
            "id": "discovery_root",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["discovery_header", "discovery_divider_1"]
                    }
                }
            }
        },
        {
            "id": "discovery_header",
            "component": {
                "Text": {
                    "text": { "literalString": "Quarantined Files" },
                    "usageHint": "header"
                }
            }
        },
        {
            "id": "discovery_divider_1",
            "component": {
                "Divider": {}
            }
        }
    ]

    # Add each quarantined file to the UI list
    for i, file_name in enumerate(files):
        card_id = f"file_card_{i}"
        row_id = f"file_row_{i}"
        name_id = f"file_name_{i}"
        btn_id = f"file_btn_{i}"
        btn_text_id = f"file_btn_text_{i}"

        components[0]["component"]["Column"]["children"]["explicitList"].append(card_id)

        components.extend([
            {
                "id": card_id,
                "component": {
                    "Card": {
                        "child": row_id
                    }
                }
            },
            {
                "id": row_id,
                "component": {
                    "Row": {
                        "children": {
                            "explicitList": [name_id, btn_id]
                        },
                        "distribution": "spaceAround"
                    }
                }
            },
            {
                "id": name_id,
                "component": {
                    "Text": {
                        "text": { "literalString": file_name }
                    }
                }
            },
            {
                "id": btn_id,
                "component": {
                    "Button": {
                        "child": btn_text_id,
                        "action": {
                            "name": "submit",
                            "context": [
                                {
                                    "key": "message",
                                    "value": { "literalString": f"Inspect {file_name}" }
                                }
                            ]
                        }
                    }
                }
            },
            {
                "id": btn_text_id,
                "component": {
                    "Text": {
                        "text": { "literalString": "Inspect & Repair" }
                    }
                }
            }
        ])

    payload = {
        "a2ui_messages": [
            {
                "surfaceUpdate": {
                    "surfaceId": "main",
                    "components": components
                }
            },
            {
                "beginRendering": {
                    "surfaceId": "main",
                    "root": "discovery_root"
                }
            }
        ]
    }
    return "---a2ui_JSON---\n" + json.dumps(payload, indent=2)

def get_repair_ui(file_name: str, errors: List[Dict[str, Any]], raw_csv_rows: List[List[str]]) -> str:
    """Generates the A2UI JSON payload for the interactive data repair form with a SINGLE global submit button."""
    
    # Find unique error row numbers
    error_rows = sorted(list(set([err["row"] for err in errors])))
    
    components = [
        {
            "id": "repair_root",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["repair_header", "repair_divider_1"]
                    }
                }
            }
        },
        {
            "id": "repair_header",
            "component": {
                "Text": {
                    "text": { "literalString": f"Repair {file_name}" },
                    "usageHint": "header"
                }
            }
        },
        {
            "id": "repair_divider_1",
            "component": {
                "Divider": {}
            }
        }
    ]

    model_contents = []
    
    # Initialize the global button context to pass all fields back to the server
    global_button_context = [
        {
            "key": "message",
            "value": { "literalString": f"Submit corrections for {file_name}" }
        },
        {
            "key": "file_name",
            "value": { "literalString": file_name }
        }
    ]

    for r_num in error_rows:
        # Get current row cells
        if r_num <= len(raw_csv_rows):
            row_data = raw_csv_rows[r_num - 1]
        else:
            row_data = ["", "", "", ""]
            
        # Ensure row_data has exactly 4 elements
        while len(row_data) < 4:
            row_data.append("")

        card_id = f"row_card_{r_num}"
        col_id = f"row_col_{r_num}"
        header_id = f"row_header_{r_num}"
        fields_row_id = f"row_fields_{r_num}"

        # Add card to root column
        components[0]["component"]["Column"]["children"]["explicitList"].append(card_id)

        # Build list of error warnings for this row
        row_errors = [err for err in errors if err["row"] == r_num]
        error_comp_ids = []
        error_comps = []
        for j, err in enumerate(row_errors):
            err_text_id = f"row_err_{r_num}_{j}"
            error_comp_ids.append(err_text_id)
            error_comps.append({
                "id": err_text_id,
                "component": {
                    "Text": {
                        "text": { "literalString": f"⚠️ Row {r_num}: {err['reason']}" }
                    }
                }
            })

        # Define data model pre-population values
        model_contents.extend([
            { "key": f"/row_{r_num}/date", "valueString": row_data[0] },
            { "key": f"/row_{r_num}/location", "valueString": row_data[1] },
            { "key": f"/row_{r_num}/product_line", "valueString": row_data[2] },
            { "key": f"/row_{r_num}/sales", "valueString": row_data[3] }
        ])

        # Dynamically append row-level text field paths to the single global button context
        global_button_context.extend([
            { "key": f"row_{r_num}_date", "value": { "path": f"/row_{r_num}/date" } },
            { "key": f"row_{r_num}_location", "value": { "path": f"/row_{r_num}/location" } },
            { "key": f"row_{r_num}_product_line", "value": { "path": f"/row_{r_num}/product_line" } },
            { "key": f"row_{r_num}_sales", "value": { "path": f"/row_{r_num}/sales" } }
        ])

        # Define TextField IDs
        tf_date = f"tf_date_{r_num}"
        tf_loc = f"tf_location_{r_num}"
        tf_prod = f"tf_product_{r_num}"
        tf_sales = f"tf_sales_{r_num}"

        row_col_children = [header_id] + error_comp_ids + [fields_row_id]

        components.extend([
            {
                "id": card_id,
                "component": {
                    "Card": {
                        "child": col_id
                    }
                }
            },
            {
                "id": col_id,
                "component": {
                    "Column": {
                        "children": {
                            "explicitList": row_col_children
                        }
                    }
                }
            },
            {
                "id": header_id,
                "component": {
                    "Text": {
                        "text": { "literalString": f"Row {r_num} - Validation Failures" },
                        "usageHint": "header"
                    }
                }
            }
        ])

        # Add the error message components
        components.extend(error_comps)

        # Add row fields
        components.extend([
            {
                "id": fields_row_id,
                "component": {
                    "Row": {
                        "children": {
                            "explicitList": [tf_date, tf_loc, tf_prod, tf_sales]
                        }
                    }
                }
            },
            {
                "id": tf_date,
                "component": {
                    "TextField": {
                        "text": { "path": f"/row_{r_num}/date" },
                        "label": { "literalString": "Date" }
                    }
                }
            },
            {
                "id": tf_loc,
                "component": {
                    "TextField": {
                        "text": { "path": f"/row_{r_num}/location" },
                        "label": { "literalString": "Location" }
                    }
                }
            },
            {
                "id": tf_prod,
                "component": {
                    "TextField": {
                        "text": { "path": f"/row_{r_num}/product_line" },
                        "label": { "literalString": "Product Line" }
                    }
                }
            },
            {
                "id": tf_sales,
                "component": {
                    "TextField": {
                        "text": { "path": f"/row_{r_num}/sales" },
                        "label": { "literalString": "Sales" }
                    }
                }
            }
        ])

    # Append a SINGLE global submit button and callout card at the very bottom of the root column
    components[0]["component"]["Column"]["children"]["explicitList"].extend([
        "global_divider", 
        "global_submit_btn", 
        "upload_callout_card"
    ])
    
    components.extend([
        {
            "id": "global_divider",
            "component": {
                "Divider": {}
            }
        },
        {
            "id": "global_submit_btn",
            "component": {
                "Button": {
                    "child": "global_submit_text",
                    "action": {
                        "name": "submit",
                        "context": global_button_context
                    }
                }
            }
        },
        {
            "id": "global_submit_text",
            "component": {
                "Text": {
                    "text": { "literalString": "Submit All Fixes" }
                }
            }
        },
        {
            "id": "upload_callout_card",
            "component": {
                "Card": {
                    "child": "upload_callout_text"
                }
            }
        },
        {
            "id": "upload_callout_text",
            "component": {
                "Text": {
                    "text": { "literalString": "💡 Or: Drag-and-drop or upload a corrected CSV file directly into the chat bar below to replace this file." }
                }
            }
        }
    ])

    payload = {
        "a2ui_messages": [
            {
                "surfaceUpdate": {
                    "surfaceId": "main",
                    "components": components
                }
            },
            {
                "dataModelUpdate": {
                    "surfaceId": "main",
                    "contents": model_contents
                }
            },
            {
                "beginRendering": {
                    "surfaceId": "main",
                    "root": "repair_root"
                }
            }
        ]
    }
    return "---a2ui_JSON---\n" + json.dumps(payload, indent=2)

def get_success_ui(file_name: str) -> str:
    """Generates the A2UI JSON payload for successful file resolution."""
    payload = {
        "a2ui_messages": [
            {
                "surfaceUpdate": {
                    "surfaceId": "main",
                    "components": [
                        {
                            "id": "success_root",
                            "component": {
                                "Card": {
                                    "child": "success_col"
                                }
                            }
                        },
                        {
                            "id": "success_col",
                            "component": {
                                "Column": {
                                    "children": {
                                        "explicitList": ["success_header", "success_detail"]
                                    }
                                }
                            }
                        },
                        {
                            "id": "success_header",
                            "component": {
                                "Text": {
                                    "text": { "literalString": f"✅ {file_name} - Resolved" },
                                    "usageHint": "header"
                                }
                            }
                        },
                        {
                            "id": "success_detail",
                            "component": {
                                "Text": {
                                    "text": { "literalString": "Status: Success | Ingested to pipeline" }
                                }
                            }
                        }
                    ]
                }
            },
            {
                "beginRendering": {
                    "surfaceId": "main",
                    "root": "success_root"
                }
            }
        ]
    }
    return "---a2ui_JSON---\n" + json.dumps(payload, indent=2)
