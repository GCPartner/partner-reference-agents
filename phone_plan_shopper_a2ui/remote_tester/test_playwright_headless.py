import os
import time
from playwright.sync_api import sync_playwright

def run_test():
    print("Launching headless browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to local proxy server serving index.html...")
        page.goto("http://localhost:8000/")
        
        print("Waiting for page load...")
        page.wait_for_selector("text=A2UI Remote Tester")
        time.sleep(1)
        
        # 1. Type "hi" and send
        print("Sending message: 'hi'")
        page.fill("input#input", "hi")
        time.sleep(0.5)
        page.click("button:has-text('Send')")
        
        # Wait for agent greeting message to appear
        print("Waiting for agent to respond with greeting UI...")
        page.wait_for_selector("text=Hi! I can help you find phone plans.", timeout=60000)
        time.sleep(1)
        
        # 2. Check category options (Plans & Devices) and click 'Start Shopping'
        print("Checking category options...")
        page.check("#shop_plans_checkbox")
        time.sleep(0.2)
        page.check("#shop_devices_checkbox")
        time.sleep(0.5)
        
        print("Clicking Start Shopping button...")
        page.click("button:has-text('Start Shopping')")
        
        # Wait for needs assessment form to appear
        print("Waiting for Needs Assessment UI...")
        page.wait_for_selector("text=Tell me about your phone plan needs.", timeout=60000)
        time.sleep(1)
        
        # 3. Form is displayed. Click 'Find Match'
        print("Selecting 'Find Match'...")
        page.click("button:has-text('Find Match')")
        
        # Wait for plans list
        print("Waiting for plans list...")
        page.wait_for_selector("text=Please select a plan:", timeout=60000)
        time.sleep(1)
        
        # Click 'Select' next to one of the plans
        print("Selecting Premium International plan...")
        select_buttons = page.locator("#chat > div").last.locator("button:has-text('Select')")
        print(f"Found {select_buttons.count()} Select buttons in latest message.")
        if select_buttons.count() >= 2:
            select_buttons.nth(1).click()
        else:
            select_buttons.first.click()
            
        # Wait for devices list
        print("Waiting for devices list...")
        page.wait_for_selector("text=Please select a device:", timeout=60000)
        time.sleep(1)
        
        # Click 'Select' next to one of the devices
        print("Selecting Google Pixel 9 device...")
        device_select_buttons = page.locator("#chat > div").last.locator("button:has-text('Select')")
        print(f"Found {device_select_buttons.count()} Device Select buttons in latest message.")
        device_select_buttons.first.click()
        
        # Wait for order summary card
        print("Waiting for Order Summary...")
        page.wait_for_selector("text=Order Summary", timeout=60000)
        time.sleep(1)
        
        # Click 'Place Order'
        print("Placing order...")
        page.locator("#chat > div").last.locator("button:has-text('Place Order')").click()
        
        # Wait for Order Confirmed card
        print("Waiting for confirmation...")
        page.wait_for_selector("text=Order Confirmed!", timeout=60000)
        time.sleep(2)
        
        print("✓ E2E Flow completed successfully in headless browser!")
        browser.close()

if __name__ == "__main__":
    run_test()
