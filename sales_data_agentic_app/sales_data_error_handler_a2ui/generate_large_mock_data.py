import os
import csv
from datetime import datetime, timedelta
import random
from google.cloud import storage

# Configure bucket names
SOURCE_BUCKET = "agentspace-demo-1145-b-sales-data"
ERROR_BUCKET = "agentspace-demo-1145-b-sales-data-errors"
PROJECT_ID = "agentspace-demo-1145-b"

clean_states = [
    "Oregon", "Washington", "Nevada", "Arizona", "Colorado", "Utah", 
    "Illinois", "Ohio", "Michigan", "Pennsylvania", "Massachusetts", 
    "North Carolina", "Virginia", "Tennessee", "Indiana"
]

error_states = [
    "Wisconsin", "Minnesota", "Missouri", "Alabama", "Louisiana", "Kentucky", "Maryland"
]

product_lines = ["Electronics", "Apparel", "Home & Kitchen", "Automotive", "Sports & Outdoors"]

def generate_row(state_name, date_override=None, sales_override=None):
    date_val = date_override or (datetime(2026, 6, 1) + timedelta(days=random.randint(0, 20))).strftime("%Y-%m-%d")
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
    print("Generating large mock dataset for 22 states...")
    
    # 1. Generate and upload clean files (15 states)
    for state in clean_states:
        file_name = f"sales_{state.lower().replace(' ', '_')}_clean.csv"
        rows = []
        # 3 to 6 rows per file
        for _ in range(random.randint(3, 6)):
            rows.append(generate_row(state))
        upload_to_gcs(SOURCE_BUCKET, file_name, rows)
        
    # 2. Generate and upload erroneous files (7 states)
    # File 1: Wisconsin - Negative sales
    wi_rows = [
        generate_row("Wisconsin"),
        generate_row("Wisconsin", sales_override=-150.0), # Error: Negative sales
        generate_row("Wisconsin")
    ]
    upload_to_gcs(ERROR_BUCKET, "sales_wisconsin_errors.csv", wi_rows)

    # File 2: Minnesota - Invalid date format
    mn_rows = [
        generate_row("Minnesota"),
        generate_row("Minnesota", date_override="06/15/2026"), # Error: Wrong date format
        generate_row("Minnesota")
    ]
    upload_to_gcs(ERROR_BUCKET, "sales_minnesota_errors.csv", mn_rows)

    # File 3: Missouri - Row with too many columns
    mo_rows = [
        generate_row("Missouri"),
        ["2026-06-10", "Missouri", "Electronics", "5500.00", "ExtraColumn"], # Error: Row too long
        generate_row("Missouri")
    ]
    upload_to_gcs(ERROR_BUCKET, "sales_missouri_errors.csv", mo_rows)

    # File 4: Alabama - Non-numeric sales amount
    al_rows = [
        generate_row("Alabama"),
        generate_row("Alabama", sales_override="NOT_A_NUMBER"), # Error: String sales
        generate_row("Alabama")
    ]
    upload_to_gcs(ERROR_BUCKET, "sales_alabama_errors.csv", al_rows)

    # File 5: Louisiana - Combination of errors (Negative sales + wrong date)
    la_rows = [
        generate_row("Louisiana", date_override="2026.06.20"), # Error: Wrong date
        generate_row("Louisiana", sales_override=-50.25), # Error: Negative sales
        generate_row("Louisiana")
    ]
    upload_to_gcs(ERROR_BUCKET, "sales_louisiana_errors.csv", la_rows)

    # File 6: Kentucky - Missing columns
    ky_rows = [
        generate_row("Kentucky"),
        ["2026-06-12", "Kentucky", "Apparel"], # Error: Missing sales column
        generate_row("Kentucky")
    ]
    upload_to_gcs(ERROR_BUCKET, "sales_kentucky_errors.csv", ky_rows)

    # File 7: Maryland - Empty fields and negative sales
    md_rows = [
        generate_row("Maryland"),
        generate_row("Maryland", sales_override=-1250.00), # Error: Negative sales
        ["", "Maryland", "Home & Kitchen", "400.00"] # Error: Empty date field
    ]
    upload_to_gcs(ERROR_BUCKET, "sales_maryland_errors.csv", md_rows)

    print("✔ Mock dataset generation and upload complete!")

if __name__ == "__main__":
    main()
