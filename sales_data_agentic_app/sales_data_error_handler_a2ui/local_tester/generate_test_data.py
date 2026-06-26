import os
from google.cloud import storage

def generate_and_upload():
    project_id = "agentspace-demo-1145-b"
    source_bucket_name = "agentspace-demo-1145-b-sales-data"
    
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(source_bucket_name)
    
    # 1. California file (with date and negative sales errors)
    california_data = (
        "date,location,product_line,sales\n"
        "06/25/2026,California,Electronics,1500.0\n"
        "2026-06-25,California,Furniture,-1250.0\n"
    )
    blob_ca = bucket.blob("sales_california_errors.csv")
    blob_ca.upload_from_string(california_data, content_type="text/csv")
    print("Uploaded sales_california_errors.csv to source GCS bucket (contains 2 errors).")

    # 2. Texas file (with column count and non-numeric sales errors)
    texas_data = (
        "date,location,product_line,sales\n"
        "2026-06-25,Texas,,850.0\n"
        "2026-06-25,Texas,Electronics,abc\n"
    )
    blob_tx = bucket.blob("sales_texas_errors.csv")
    blob_tx.upload_from_string(texas_data, content_type="text/csv")
    print("Uploaded sales_texas_errors.csv to source GCS bucket (contains 2 errors).")

    # 3. Florida file (completely valid)
    florida_data = (
        "date,location,product_line,sales\n"
        "2026-06-25,Florida,Electronics,3400.0\n"
        "2026-06-25,Florida,Furniture,2100.0\n"
    )
    blob_fl = bucket.blob("sales_florida_valid.csv")
    blob_fl.upload_from_string(florida_data, content_type="text/csv")
    print("Uploaded sales_florida_valid.csv to source GCS bucket (100% valid).")

    # 4. Illinois file (completely valid)
    illinois_data = (
        "date,location,product_line,sales\n"
        "2026-06-25,Illinois,Electronics,1800.0\n"
        "2026-06-25,Illinois,Furniture,1200.0\n"
    )
    blob_il = bucket.blob("sales_illinois_valid.csv")
    blob_il.upload_from_string(illinois_data, content_type="text/csv")
    print("Uploaded sales_illinois_valid.csv to source GCS bucket (100% valid).")

if __name__ == "__main__":
    generate_and_upload()
