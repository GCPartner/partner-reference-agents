import os
import time
from playwright.sync_api import sync_playwright

# Set display environment variable for CRD session
os.environ["DISPLAY"] = ":20"

def run_test():
    print("Launching visible browser on DISPLAY=:20...")
    with sync_playwright() as p:
        # Launch Chromium with headless=False so user can watch it
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--start-maximized"
            ]
        )
        
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        
        print("Navigating to local proxy server serving index.html...")
        page.goto("http://localhost:8000/")
        
        print("Waiting for page load...")
        page.wait_for_selector("text=A2UI Remote Tester")
        time.sleep(2)  # Pause to let the user see it
        
        # 1. Type "hi" and send
        print("Sending message: 'hi'")
        page.fill("input#input", "hi")
        time.sleep(1)
        page.click("button:has-text('Send')")
        
        # Wait for agent greeting message to appear
        print("Waiting for agent to respond with greeting UI...")
        page.wait_for_selector("text=Hi! I can help you find phone plans.", timeout=60000)
        time.sleep(3)
        
        # 2. Check category options (Plans & Devices) and click 'Start Shopping'
        print("Checking category options...")
        # Checkboxes are rendered. We check the inputs.
        page.check("#shop_plans_checkbox")
        time.sleep(0.5)
        page.check("#shop_devices_checkbox")
        time.sleep(1.5)
        
        print("Clicking Start Shopping button...")
        page.click("button:has-text('Start Shopping')")
        
        # Wait for needs assessment form to appear
        print("Waiting for Needs Assessment UI...")
        page.wait_for_selector("text=Tell me about your phone plan needs.", timeout=60000)
        time.sleep(3)
        
        # 3. Form is displayed. Let's adjust sliders/inputs if desired, or click 'Find Match'
        print("Selecting 'Find Match'...")
        page.click("button:has-text('Find Match')")
        
        # Wait for plans list
        print("Waiting for plans list...")
        page.wait_for_selector("text=Please select a plan:", timeout=60000)
        time.sleep(4)
        
        # Click 'Select' next to one of the plans (e.g. Premium International)
        print("Selecting Premium International plan...")
        # Get select buttons in the latest message container only
        select_buttons = page.locator("#chat > div").last.locator("button:has-text('Select')")
        print(f"Found {select_buttons.count()} Select buttons in latest message.")
        if select_buttons.count() >= 2:
            select_buttons.nth(1).click()  # Select the second plan
        else:
            select_buttons.first.click()
            
        # Wait for devices list
        print("Waiting for devices list...")
        page.wait_for_selector("text=Please select a device:", timeout=60000)
        time.sleep(4)
        
        # Click 'Select' next to one of the devices (e.g. Google Pixel 9)
        print("Selecting Google Pixel 9 device...")
        device_select_buttons = page.locator("#chat > div").last.locator("button:has-text('Select')")
        print(f"Found {device_select_buttons.count()} Device Select buttons in latest message.")
        device_select_buttons.first.click()  # Click first Select button (Pixel 9)
        
        # Wait for order summary card
        print("Waiting for Order Summary...")
        page.wait_for_selector("text=Order Summary", timeout=60000)
        time.sleep(3)  # Wait to inspect initial order summary card
        
        # Type "too expensive" to negotiate a discount
        print("Sending message: 'too expensive'")
        page.fill("input#input", "too expensive")
        time.sleep(1)
        page.click("button:has-text('Send')")
        
        # Wait for discount request dialog
        print("Waiting for discount request dialog...")
        page.wait_for_selector("text=Would you like me to request a manager discount for you?", timeout=60000)
        time.sleep(3)
        
        # Click 'Yes'
        print("Clicking Yes on discount card...")
        page.locator("#chat > div").last.locator("button:has-text('Yes')").click()
        
        # Wait for updated order summary with discount
        print("Waiting for updated Order Summary (15% discount applied)...")
        page.wait_for_selector("text=discounted to", timeout=60000)
        time.sleep(5)  # Pause to let the user see the discounted prices and verify no auto-confirm
        
        # Click 'Place Order'
        print("Placing order with discount...")
        page.locator("#chat > div").last.locator("button:has-text('Place Order')").click()
        
        # Wait for Order Confirmed card
        print("Waiting for confirmation...")
        page.wait_for_selector("text=Order Confirmed!", timeout=60000)
        time.sleep(5)
        
        print("Flow completed successfully! Keeping the browser window open for 15 minutes so you can inspect the confirmation UI...")
        time.sleep(900)
        browser.close()

if __name__ == "__main__":
    run_test()
