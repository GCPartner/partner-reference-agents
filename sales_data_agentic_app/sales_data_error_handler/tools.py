import os
import csv
from typing import Dict, List, Any
from datetime import datetime
from google.cloud import storage
from google.adk.tools.tool_context import ToolContext

# Configurable bucket names
SOURCE_BUCKET = os.environ.get("SOURCE_BUCKET", "partner-engg-agents-sales-data")
ERROR_BUCKET = os.environ.get("ERROR_BUCKET", "partner-engg-agents-sales-data-errors")

def list_quarantined_files(tool_context: ToolContext = None) -> Dict[str, Any]:
    """Scans the error GCS bucket for quarantined sales CSV files.

    Returns:
        A dict containing 'status' ('success' or 'error') and a list of file names in 'files'.
    """
    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "agentspace-demo-1145-b")
        client = storage.Client(project=project_id)
        bucket = client.bucket(ERROR_BUCKET)
        
        blobs = bucket.list_blobs()
        files = [blob.name for blob in blobs if blob.name.endswith(".csv")]
        
        return {
            "status": "success",
            "files": files
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to list quarantined files: {str(e)}"
        }

def download_quarantined_file(file_name: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """Downloads the complete raw content of a quarantined CSV file from the error bucket.

    Args:
        file_name: The name of the quarantined file to download.

    Returns:
        A dict containing 'status' ('success' or 'error') and the raw text 'content' of the CSV.
    """
    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "agentspace-demo-1145-b")
        client = storage.Client(project=project_id)
        bucket = client.bucket(ERROR_BUCKET)
        blob = bucket.blob(file_name)

        if not blob.exists():
            return {
                "status": "error",
                "message": f"File {file_name} does not exist in GCS error bucket."
            }

        content = blob.download_as_text()
        return {
            "status": "success",
            "content": content
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to download quarantined file: {str(e)}"
        }

def analyze_file_errors(file_name: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """Downloads a quarantined sales CSV file from the error bucket and validates it.
    
    It identifies and returns all schema and row-level errors in the file.

    Args:
        file_name: The name of the quarantined CSV file in the error bucket.

    Returns:
        A dict containing 'status' ('invalid' or 'valid' or 'error') and a list of 'errors'
        with row numbers, values, and validation failure reasons.
    """
    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "agentspace-demo-1145-b")
        client = storage.Client(project=project_id)
        bucket = client.bucket(ERROR_BUCKET)
        blob = bucket.blob(file_name)

        if not blob.exists():
            return {
                "status": "error",
                "message": f"File {file_name} does not exist in GCS error bucket."
            }

        content = blob.download_as_text()
        reader = csv.reader(content.splitlines())
        
        try:
            headers = next(reader)
        except StopIteration:
            return {
                "status": "invalid",
                "errors": [{"row": 1, "value": "", "reason": "File is empty."}]
            }

        expected_headers = ["date", "location", "product_line", "sales"]
        headers = [h.strip().lower() for h in headers]
        if headers != expected_headers:
            return {
                "status": "invalid",
                "errors": [{"row": 1, "value": str(headers), "reason": f"Invalid headers. Expected {expected_headers}, got {headers}."}]
            }

        errors = []
        line_num = 1
        for row in reader:
            line_num += 1
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
            return {
                "status": "invalid",
                "errors": errors
            }
            
        return {
            "status": "valid",
            "message": "No errors found in file."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to analyze file: {str(e)}"
        }

def submit_corrections(file_name: str, corrected_content: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """Validates the corrected CSV content and, if 100% valid, moves it to the source bucket.

    It deletes the corrected file from the error bucket upon successful resubmission.

    Args:
        file_name: The name of the file to correct and resubmit.
        corrected_content: The complete corrected CSV contents as a string.

    Returns:
        A dict indicating 'status' ('success' or 'error') and details.
    """
    try:
        # 1. Validate the corrected content first
        reader = csv.reader(corrected_content.splitlines())
        try:
            headers = next(reader)
        except StopIteration:
            return {
                "status": "error",
                "message": "Validation failed: Corrected content is empty."
            }

        expected_headers = ["date", "location", "product_line", "sales"]
        headers = [h.strip().lower() for h in headers]
        if headers != expected_headers:
            return {
                "status": "error",
                "message": f"Validation failed: Invalid headers. Expected {expected_headers}, got {headers}."
            }

        line_num = 1
        for row in reader:
            line_num += 1
            if not row:
                continue
            if len(row) != 4:
                return {
                    "status": "error",
                    "message": f"Validation failed at row {line_num}: Expected 4 columns, got {len(row)}."
                }

            date_str, location, product_line, sales_str = [cell.strip() for cell in row]

            # Validate date
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Validation failed at row {line_num}: Invalid date format '{date_str}'. Expected YYYY-MM-DD."
                }

            # Validate sales
            try:
                sales_val = float(sales_str)
                if sales_val < 0:
                    return {
                        "status": "error",
                        "message": f"Validation failed at row {line_num}: Sales amount cannot be negative."
                    }
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Validation failed at row {line_num}: Invalid numeric sales amount '{sales_str}'."
                }

        # 2. If 100% valid, upload to SOURCE_BUCKET and delete from ERROR_BUCKET
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "agentspace-demo-1145-b")
        client = storage.Client(project=project_id)
        
        source_bucket = client.bucket(SOURCE_BUCKET)
        error_bucket = client.bucket(ERROR_BUCKET)
        
        # Upload corrected content to source bucket
        dest_blob = source_bucket.blob(file_name)
        dest_blob.upload_from_string(corrected_content, content_type="text/csv")
        
        # Delete from error bucket
        error_blob = error_bucket.blob(file_name)
        if error_blob.exists():
            error_blob.delete()
            
        return {
            "status": "success",
            "message": f"File {file_name} successfully corrected, validated, and resubmitted to the processing pipeline."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to submit corrections: {str(e)}"
        }
