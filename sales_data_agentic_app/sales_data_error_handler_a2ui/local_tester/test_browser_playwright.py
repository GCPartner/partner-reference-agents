import asyncio
import os
from playwright.async_api import async_playwright
from google.cloud import storage

async def run_browser_test():
    project_id = "agentspace-demo-1145-b"
    error_bucket_name = "agentspace-demo-1145-b-sales-data-errors"
    source_bucket_name = "agentspace-demo-1145-b-sales-data"
    
    # 1. Setup fresh mock quarantined file in GCS error bucket
    storage_client = storage.Client(project=project_id)
    error_bucket = storage_client.bucket(error_bucket_name)
    source_bucket = storage_client.bucket(source_bucket_name)
    
    # Clean up old source blob if any
    source_blob = source_bucket.blob("sales_california_errors.csv")
    if source_blob.exists():
        source_blob.delete()
        print("Cleaned up existing sales_california_errors.csv from source bucket.")
        
    # Upload fresh mock errors file to GCS error bucket
    mock_content = (
        "date,location,product_line,sales\n"
        "06/25/2026,California,Electronics,1500.0\n"
        "2026-06-25,California,Furniture,-1250.0\n"
    )
    error_blob = error_bucket.blob("sales_california_errors.csv")
    error_blob.upload_from_string(mock_content, content_type="text/csv")
    print("Uploaded fresh sales_california_errors.csv to GCS error bucket.")

    # 2. Launch browser automation
    async with async_playwright() as p:
        print("Launching headed browser...")
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(viewport={"width": 1000, "height": 900})
        page = await context.new_page()
        
        print("Navigating to local A2UI tester server...")
        await page.goto("http://localhost:8005/")
        await asyncio.sleep(2)
        await page.screenshot(path="step1_load.png")
        print("✔ Screenshot 1 saved: step1_load.png")
        
        # Type 'hi' to trigger greeting
        print("Sending greeting 'hi'...")
        await page.fill("input[id='input']", "hi")
        await page.press("input[id='input']", "Enter")
        
        # Wait for agent response and A2UI card
        print("Waiting for discovery dashboard...")
        await asyncio.sleep(8)
        await page.screenshot(path="step2_greeting.png")
        print("✔ Screenshot 2 saved: step2_greeting.png")
        
        # Click Inspect & Repair button
        print("Clicking 'Inspect & Repair' button...")
        inspect_btn = page.get_by_role("button", name="Inspect & Repair").first
        await inspect_btn.click()
        
        # Wait for repair form with multiple rows to render
        print("Waiting for repair form...")
        await asyncio.sleep(8)
        await page.screenshot(path="step3_form_rendered.png")
        print("✔ Screenshot 3 saved: step3_form_rendered.png")
        
        # Edit Row 2 (Date: 06/25/2026 -> 2026-06-25)
        print("Editing Row 2 date field...")
        date_input = page.locator("input[id='/row_2/date']")
        await date_input.fill("") # Clear first
        await date_input.fill("2026-06-25")
        
        # Edit Row 3 (Sales: -1250.0 -> 1250.0)
        print("Editing Row 3 sales field...")
        sales_input = page.locator("input[id='/row_3/sales']")
        await sales_input.fill("") # Clear first
        await sales_input.fill("1250.0")
        
        await asyncio.sleep(1)
        await page.screenshot(path="step4_form_edited.png")
        print("✔ Screenshot 4 saved: step4_form_edited.png")
        
        # Click the SINGLE global Submit All Fixes button!
        print("Clicking global 'Submit All Fixes' button...")
        submit_btn = page.get_by_role("button", name="Submit All Fixes")
        await submit_btn.click()
        
        # Wait for success card
        print("Waiting for success card...")
        await asyncio.sleep(8)
        await page.screenshot(path="step5_success.png")
        print("✔ Screenshot 5 saved: step5_success.png")
        
        await browser.close()
        print("Browser closed. E2E browser test completed successfully.")
        
        # Verify physical GCS bucket state transitions
        storage_client_check = storage.Client(project=project_id)
        error_bucket_check = storage_client_check.bucket(error_bucket_name)
        source_bucket_check = storage_client_check.bucket(source_bucket_name)
        
        error_blob_exists = error_bucket_check.blob("sales_california_errors.csv").exists()
        source_blob_exists = source_bucket_check.blob("sales_california_errors.csv").exists()
        
        print(f"Post-test GCS check:")
        print(f"  - sales_california_errors.csv in error bucket: {error_blob_exists} (Expected: False)")
        print(f"  - sales_california_errors.csv in source bucket: {source_blob_exists} (Expected: True)")
        
        assert not error_blob_exists, "Quarantined file was not deleted from error GCS bucket!"
        assert source_blob_exists, "Corrected file was not resubmitted to source GCS bucket!"
        print("✔ E2E GCS state transitions verified successfully!")

if __name__ == "__main__":
    asyncio.run(run_browser_test())
