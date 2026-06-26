import os
from google.cloud import storage

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "partner-engg-agents")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
SOURCE_BUCKET = os.environ.get("SOURCE_BUCKET", f"{PROJECT_ID}-sales-data")
ERROR_BUCKET = os.environ.get("ERROR_BUCKET", f"{PROJECT_ID}-sales-data-errors")
ARCHIVE_BUCKET = os.environ.get("ARCHIVE_BUCKET", f"{PROJECT_ID}-sales-data-archive")

MOCK_FILES = [
    "sales_boston_20260618.csv",
    "sales_chicago_20260618.csv",
    "sales_ny_invalid_schema.csv",
    "sales_sf_invalid_data.csv"
]

def setup_gcs():
    print("Initializing Storage Client...")
    client = storage.Client(project=PROJECT_ID)

    # Helper function to create bucket if not exists
    def create_bucket_if_not_exists(bucket_name):
        bucket = client.bucket(bucket_name)
        if not bucket.exists():
            print(f"Creating bucket {bucket_name} in {LOCATION}...")
            client.create_bucket(bucket, location=LOCATION)
            print(f"Bucket {bucket_name} created successfully.")
        else:
            print(f"Bucket {bucket_name} already exists.")
        return bucket

    source_bucket = create_bucket_if_not_exists(SOURCE_BUCKET)
    create_bucket_if_not_exists(ERROR_BUCKET)
    create_bucket_if_not_exists(ARCHIVE_BUCKET)

    # Upload files
    dir_path = os.path.dirname(os.path.abspath(__file__))
    for file_name in MOCK_FILES:
        local_file_path = os.path.join(dir_path, file_name)
        if os.path.exists(local_file_path):
            blob = source_bucket.blob(file_name)
            print(f"Uploading {file_name} to gs://{SOURCE_BUCKET}/{file_name}...")
            blob.upload_from_filename(local_file_path)
            print(f"Uploaded {file_name} successfully.")
        else:
            print(f"Error: Local file {local_file_path} not found.")

if __name__ == "__main__":
    setup_gcs()
