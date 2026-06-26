import os
import csv
from datetime import datetime
from typing import Dict, List, Any
import sqlalchemy
from google.cloud import storage
from google.cloud.sql.connector import Connector, IPTypes
from google.adk.tools.tool_context import ToolContext

# Configurable bucket names
SOURCE_BUCKET = os.environ.get("SOURCE_BUCKET", "partner-engg-agents-sales-data")
ERROR_BUCKET = os.environ.get("ERROR_BUCKET", "partner-engg-agents-sales-data-errors")
ARCHIVE_BUCKET = os.environ.get("ARCHIVE_BUCKET", "partner-engg-agents-sales-data-archive")

_pool = None

def get_secret(secret_name: str) -> str:
    """Retrieves a secret from environment variables, local files, or Secret Manager."""
    # 1. Check environment variables (supports secret_storage=file)
    val = os.environ.get(secret_name)
    if val:
        return val

    # 2. Check local secrets directory
    secret_file_path = f"secrets/{secret_name}"
    if os.path.exists(secret_file_path):
        try:
            with open(secret_file_path, "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading local secret file {secret_name}: {e}")

    # 3. Fallback to Secret Manager
    try:
        from google.cloud import secretmanager
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "partner-engg-agents")
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        print(f"Could not load secret {secret_name} from Secret Manager: {e}")

    return ""

def get_connection_pool():
    """Initializes and returns a SQLAlchemy connection pool to Cloud SQL."""
    global _pool
    if _pool:
        return _pool

    connection_name = get_secret("DB_CONNECTION_NAME")
    db_user = get_secret("DB_USER")
    db_pass = get_secret("DB_PASSWORD")
    db_name = get_secret("DB_NAME")

    if not all([connection_name, db_user, db_pass, db_name]):
        raise ValueError(
            "Database connection parameters are missing. Please configure "
            "DB_CONNECTION_NAME, DB_USER, DB_PASSWORD, and DB_NAME."
        )

    connector = Connector()

    def getconn():
        return connector.connect(
            connection_name,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=IPTypes.PUBLIC,
        )

    _pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return _pool

def list_sales_files(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Scans the source GCS bucket for new CSV files.

    Returns:
        A dict containing 'status' and a list of file names in 'files'.
    """
    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "partner-engg-agents")
        client = storage.Client(project=project_id)
        bucket = client.bucket(SOURCE_BUCKET)
        
        # List files ending in .csv
        blobs = bucket.list_blobs()
        files = [blob.name for blob in blobs if blob.name.endswith(".csv")]
        
        return {
            "status": "success",
            "files": files
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to list files: {str(e)}"
        }

def process_sales_file(file_name: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Downloads, parses, and validates a CSV sales file. Valid files are upserted into the SQL
    database and moved to the archive bucket. Invalid files are moved to the error bucket.

    Args:
        file_name: The name of the GCS object to process.

    Returns:
        A dict indicating the result and details of the operation.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "partner-engg-agents")
    client = storage.Client(project=project_id)
    source_bucket = client.bucket(SOURCE_BUCKET)
    blob = source_bucket.blob(file_name)

    if not blob.exists():
        return {
            "status": "error",
            "message": f"File {file_name} does not exist in GCS source bucket."
        }

    # Download content
    try:
        content = blob.download_as_text()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to download file: {str(e)}"
        }

    # Validate CSV content
    reader = csv.reader(content.splitlines())
    try:
        headers = next(reader)
    except StopIteration:
        _move_to_bucket(client, SOURCE_BUCKET, ERROR_BUCKET, file_name)
        return {
            "status": "rejected",
            "reason": "File is empty."
        }

    # Column/header check
    expected_headers = ["date", "location", "product_line", "sales"]
    headers = [h.strip().lower() for h in headers]
    if headers != expected_headers:
        _move_to_bucket(client, SOURCE_BUCKET, ERROR_BUCKET, file_name)
        return {
            "status": "rejected",
            "reason": f"Invalid headers. Expected {expected_headers}, got {headers}."
        }

    valid_rows = []
    line_num = 1
    for row in reader:
        line_num += 1
        if not row:
            continue
        if len(row) != 4:
            _move_to_bucket(client, SOURCE_BUCKET, ERROR_BUCKET, file_name)
            return {
                "status": "rejected",
                "reason": f"Row {line_num} has invalid column count. Expected 4 columns."
            }

        date_str, location, product_line, sales_str = [cell.strip() for cell in row]

        # Validate date format
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            _move_to_bucket(client, SOURCE_BUCKET, ERROR_BUCKET, file_name)
            return {
                "status": "rejected",
                "reason": f"Row {line_num} has invalid date '{date_str}'. Expected YYYY-MM-DD."
            }

        # Validate sales value
        try:
            sales_val = float(sales_str)
            if sales_val < 0:
                raise ValueError("Sales amount cannot be negative.")
        except ValueError as e:
            _move_to_bucket(client, SOURCE_BUCKET, ERROR_BUCKET, file_name)
            return {
                "status": "rejected",
                "reason": f"Row {line_num} has invalid sales amount '{sales_str}': {str(e)}"
            }

        valid_rows.append({
            "sales_date": parsed_date,
            "location": location,
            "product_line": product_line,
            "sales_amount": sales_val
        })

    # Ingest into Database
    try:
        pool = get_connection_pool()
        query = sqlalchemy.text("""
            INSERT INTO daily_sales (sales_date, location, product_line, sales_amount)
            VALUES (:sales_date, :location, :product_line, :sales_amount)
            ON CONFLICT (sales_date, location, product_line)
            DO UPDATE SET sales_amount = EXCLUDED.sales_amount;
        """)

        with pool.connect() as conn:
            conn.execute(query, valid_rows)
            conn.commit()
    except Exception as db_err:
        # DB failure: do not move files, let user retry later
        return {
            "status": "error",
            "message": f"Database insertion failed: {str(db_err)}"
        }

    # Move valid file to archive
    try:
        _move_to_bucket(client, SOURCE_BUCKET, ARCHIVE_BUCKET, file_name)
    except Exception as move_err:
        # If DB write succeeded but archiving fails, warn user
        return {
            "status": "warning",
            "message": f"Data saved to DB, but failed to move file to archive: {str(move_err)}"
        }

    return {
        "status": "success",
        "processed_rows": len(valid_rows)
    }

def _move_to_bucket(client: storage.Client, src_bucket_name: str, dest_bucket_name: str, blob_name: str):
    """Utility function to move a GCS object between buckets."""
    src_bucket = client.bucket(src_bucket_name)
    dest_bucket = client.bucket(dest_bucket_name)
    src_blob = src_bucket.blob(blob_name)
    
    # Copy to destination bucket
    src_bucket.copy_blob(src_blob, dest_bucket, blob_name)
    # Delete original
    src_blob.delete()
