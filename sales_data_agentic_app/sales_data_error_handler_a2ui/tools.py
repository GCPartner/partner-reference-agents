import os
import csv
from typing import Dict, List, Any
from datetime import datetime
from google.cloud import storage
from google.adk.tools.tool_context import ToolContext

# Import UI templates
from .a2ui_templates import get_discovery_ui, get_repair_ui, get_success_ui

# Configurable bucket names
SOURCE_BUCKET = os.environ.get("SOURCE_BUCKET", "partner-engg-agents-sales-data")
ERROR_BUCKET = os.environ.get("ERROR_BUCKET", "partner-engg-agents-sales-data-errors")

def list_quarantined_files(tool_context: ToolContext = None) -> Dict[str, Any]:
    """Scans the error GCS bucket for quarantined sales CSV files and generates the A2UI dashboard.

    Returns:
        A dict containing 'result' (text description + A2UI JSON payload).
    """
    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "agentspace-demo-1145-b")
        client = storage.Client(project=project_id)
        bucket = client.bucket(ERROR_BUCKET)
        
        blobs = bucket.list_blobs()
        files = [blob.name for blob in blobs if blob.name.endswith(".csv")]
        
        if not files:
            text = "I checked the GCS error bucket and it is completely clear! No files require attention."
            return {"result": text}
            
        # Generate the A2UI JSON payload
        ui_payload = get_discovery_ui(files)
        text = f"Hello! I found {len(files)} quarantined file(s) in the GCS error bucket. Please select one below to inspect:\n\n{ui_payload}"
        
        return {"result": text}
    except Exception as e:
        return {
            "result": f"Failed to list quarantined files due to an error: {str(e)}"
        }

def analyze_file_errors(file_name: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """Downloads a quarantined sales CSV file, validates it, and generates the A2UI repair form.

    Args:
        file_name: The name of the quarantined CSV file in the error bucket.

    Returns:
        A dict containing 'result' (text explanation + A2UI JSON form).
    """
    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "agentspace-demo-1145-b")
        client = storage.Client(project=project_id)
        bucket = client.bucket(ERROR_BUCKET)
        blob = bucket.blob(file_name)

        if not blob.exists():
            return {
                "result": f"Error: File {file_name} does not exist in the GCS error bucket."
            }

        content = blob.download_as_text()
        raw_csv_rows = list(csv.reader(content.splitlines()))
        
        if not raw_csv_rows:
            return {
                "result": f"Error: The quarantined file {file_name} is completely empty."
            }

        headers = [h.strip().lower() for h in raw_csv_rows[0]]
        expected_headers = ["date", "location", "product_line", "sales"]
        if headers != expected_headers:
            errors = [{"row": 1, "value": str(headers), "reason": f"Invalid headers. Expected {expected_headers}, got {headers}."}]
            ui_payload = get_repair_ui(file_name, errors, raw_csv_rows)
            text = f"I inspected '{file_name}' and found header errors. Please review and edit below:\n\n{ui_payload}"
            return {"result": text}

        errors = []
        for line_num in range(2, len(raw_csv_rows) + 1):
            row = raw_csv_rows[line_num - 1]
            if not row:
                continue
            if len(row) != 4:
                errors.append({
                    "row": line_num,
                    "value": str(row),
                    "reason": f"Row has invalid column count. Expected 4 columns, got {len(row)}."
                })
                continue

            date_str, location, product_line, sales_str = [cell.strip() for cell in row]

            # Validate date format
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                errors.append({
                    "row": line_num,
                    "value": date_str,
                    "reason": f"Invalid date format '{date_str}'. Expected YYYY-MM-DD."
                })

            # Validate sales value
            try:
                sales_val = float(sales_str)
                if sales_val < 0:
                    errors.append({
                        "row": line_num,
                        "value": sales_str,
                        "reason": "Sales amount cannot be negative."
                    })
            except ValueError:
                errors.append({
                    "row": line_num,
                    "value": sales_str,
                    "reason": f"Invalid numeric sales amount '{sales_str}'."
                })

        if errors:
            ui_payload = get_repair_ui(file_name, errors, raw_csv_rows)
            text = f"I analyzed '{file_name}' and found validation errors. Please review the failures and make your edits directly in the card below:\n\n{ui_payload}"
            return {"result": text}
            
        return {
            "result": f"Excellent news! I analyzed '{file_name}' and found no validation errors. You can resubmit it safely."
        }
        
    except Exception as e:
        return {
            "result": f"Failed to analyze file errors: {str(e)}"
        }

def submit_corrections(file_name: str, corrected_content: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """Validates the corrected CSV content and, if valid, uploads to source bucket and deletes from error bucket.

    Args:
        file_name: The name of the file to correct.
        corrected_content: The complete corrected CSV contents as a string.

    Returns:
        A dict containing 'result' (text explanation + A2UI success/error payload).
    """
    try:
        # Validate the corrected content
        reader = csv.reader(corrected_content.splitlines())
        try:
            headers = next(reader)
        except StopIteration:
            return {"result": "Validation failed: Corrected content is completely empty."}

        expected_headers = ["date", "location", "product_line", "sales"]
        headers = [h.strip().lower() for h in headers]
        if headers != expected_headers:
            return {"result": f"Validation failed: Invalid headers. Expected {expected_headers}, got {headers}."}

        line_num = 1
        for row in reader:
            line_num += 1
            if not row:
                continue
            if len(row) != 4:
                return {"result": f"Validation failed at row {line_num}: Expected 4 columns, got {len(row)}."}

            date_str, location, product_line, sales_str = [cell.strip() for cell in row]

            # Validate date
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return {"result": f"Validation failed at row {line_num}: Invalid date format '{date_str}'. Expected YYYY-MM-DD."}

            # Validate sales
            try:
                sales_val = float(sales_str)
                if sales_val < 0:
                    return {"result": f"Validation failed at row {line_num}: Sales amount cannot be negative."}
            except ValueError:
                return {"result": f"Validation failed at row {line_num}: Invalid numeric sales amount '{sales_str}'."}

        # If 100% valid, upload and delete
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "agentspace-demo-1145-b")
        client = storage.Client(project=project_id)
        
        source_bucket = client.bucket(SOURCE_BUCKET)
        error_bucket = client.bucket(ERROR_BUCKET)
        
        # Upload corrected content
        dest_blob = source_bucket.blob(file_name)
        dest_blob.upload_from_string(corrected_content, content_type="text/csv")
        
        # Delete from error bucket
        error_blob = error_bucket.blob(file_name)
        if error_blob.exists():
            error_blob.delete()
            
        # Generate A2UI success card
        ui_payload = get_success_ui(file_name)
        text = f"Great news! The file '{file_name}' has been successfully corrected, validated, and resubmitted to the processing pipeline.\n\n{ui_payload}"
        
        return {"result": text}

    except Exception as e:
        return {
            "result": f"Failed to resubmit corrected file due to an unexpected error: {str(e)}"
        }

def apply_all_fixes(file_name: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """Downloads the quarantined file, applies all row-level edits from the session state, and resubmits it.

    Args:
        file_name: The name of the file in the GCS error bucket.
    """
    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "agentspace-demo-1145-b")
        client = storage.Client(project=project_id)
        bucket = client.bucket(ERROR_BUCKET)
        blob = bucket.blob(file_name)

        if not blob.exists():
            return {"result": f"Error: File {file_name} does not exist in the GCS error bucket."}

        content = blob.download_as_text()
        rows = list(csv.reader(content.splitlines()))
        
        # Access session state containing the edited values from the button click
        raw_state = tool_context.state if (tool_context and tool_context.state) else {}
        state = raw_state.to_dict() if hasattr(raw_state, "to_dict") else raw_state
        print(f"[DEBUG] Extracted state dict: {state}")
        
        # Helper to get value matching key or prefixed key (e.g. temp:key)
        def get_state_value(k):
            if k in state:
                return state[k]
            for prefix in ["temp:", "user:", "app:"]:
                if f"{prefix}{k}" in state:
                    return state[f"{prefix}{k}"]
            for existing_key in state:
                if existing_key.endswith(f":{k}"):
                    return state[existing_key]
            return None
            
        # Loop through all rows in the file (headers are row 1, data starts at row 2)
        applied_count = 0
        for i in range(2, len(rows) + 1):
            # Look for keys like row_2_date, row_2_location, etc.
            date_val = get_state_value(f"row_{i}_date")
            location_val = get_state_value(f"row_{i}_location")
            product_val = get_state_value(f"row_{i}_product_line")
            sales_val = get_state_value(f"row_{i}_sales")
            print(f"[DEBUG] Row {i} checks - date: {date_val}, location: {location_val}, product: {product_val}, sales: {sales_val}")
            
            # If any corrections are found in the state, apply them!
            if date_val is not None or location_val is not None or product_val is not None or sales_val is not None:
                current_row = rows[i - 1]
                # Fallback to current values if any field is missing in state
                new_date = date_val if date_val is not None else current_row[0]
                new_loc = location_val if location_val is not None else current_row[1]
                new_prod = product_val if product_val is not None else current_row[2]
                new_sales = sales_val if sales_val is not None else current_row[3]
                
                rows[i - 1] = [new_date, new_loc, new_prod, new_sales]
                applied_count += 1
                
        if applied_count == 0:
            return {"result": "No corrections were found in the submission state. Please edit the form fields first."}

        # Convert back to CSV text
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        corrected_csv_text = output.getvalue()
        
        # Resubmit using submit_corrections
        return submit_corrections(file_name, corrected_csv_text)
    except Exception as e:
        return {"result": f"Failed to apply corrections: {str(e)}"}


