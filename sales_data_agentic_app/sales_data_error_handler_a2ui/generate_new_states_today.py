import os
import csv
from datetime import datetime
import random
from google.cloud import storage

# Configure bucket name
SOURCE_BUCKET = "agentspace-demo-1145-b-sales-data"
PROJECT_ID = "agentspace-demo-1145-b"

# 20 Clean states (distinct from yesterday's set)
clean_states = [
    "New York", "Texas", "Florida", "Georgia", "New Jersey", 
    "West Virginia", "South Carolina", "Connecticut", "New Hampshire", "Maine", 
    "Vermont", "Delaware", "Rhode Island", "Oklahoma", "Kansas", 
    "Nebraska", "Iowa", "Arkansas", "Mississippi", "New Mexico"
]

# 2 Erroneous states
error_states = ["Idaho", "Montana"]

product_lines = ["Electronics", "Apparel", "Home & Kitchen", "Automotive", "Sports & Outdoors"]

# Today is Friday, June 26, 2026
TODAY_STR = "2026-06-26"

def generate_row(state_name, date_override=None, sales_override=None):
    date_val = date_override or TODAY_STR
    product = random.choice(product_lines)
    sales = sales_override or round(random.uniform(500.0, 15000.0), 2)
    return [date_val, state_name, product, str(sales)]

def upload_to_gcs(bucket_name, file_name, rows):
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    csv_content = ""
    # Header row
    csv_content += "date,location,product_line,sales\n"
    for r in rows:
        csv_content += ",".join(r) + "\n"
        
    blob.upload_from_string(csv_content, content_type="text/csv")
    print(f"✔ Uploaded gs://{bucket_name}/{file_name} ({len(rows)} rows)")

def main():
    print(f"Generating new sales data for 22 states for today ({TODAY_STR})...")
    
    # 1. Generate and upload clean files (20 states) to the input bucket
    for state in clean_states:
        file_name = f"sales_{state.lower().replace(' ', '_')}_today.csv"
        rows = []
        # 3 to 6 rows per file
        for _ in range(random.randint(3, 6)):
            rows.append(generate_row(state))
        upload_to_gcs(SOURCE_BUCKET, file_name, rows)
        
    # 2. Generate and upload erroneous files (2 states) to the input bucket
    # File 1: Idaho - Negative sales
    idaho_rows = [
        generate_row("Idaho"),
        generate_row("Idaho", sales_override=-850.0), # Error: Negative sales
        generate_row("Idaho")
    ]
    upload_to_gcs(SOURCE_BUCKET, "sales_idaho_today_errors.csv", idaho_rows)

    # File 2: Montana - Invalid date format
    montana_rows = [
        generate_row("Montana"),
        generate_row("Montana", date_override="06/26/2026"), # Error: Wrong date format (MM/DD/YYYY)
        generate_row("Montana")
    ]
    upload_to_gcs(SOURCE_BUCKET, "sales_montana_today_errors.csv", montana_rows)

    print("✔ Generation and upload to input bucket complete!")

if __name__ == "__main__":
    main()
