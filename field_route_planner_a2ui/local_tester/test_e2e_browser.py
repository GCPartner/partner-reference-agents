import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def run_e2e_test():
    print("Starting Playwright E2E Browser Test...")
    screenshot_path = "/Users/veermuchandi/code/rad-workshop/field_route_planner_a2ui/e2e_browser_result.png"
    
    # Ensure scratch folder exists
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser in headful mode
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1024, "height": 768})
        page = await context.new_page()
        
        # Attach console and error listeners
        page.on("console", lambda msg: print(f"Browser Console: [{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser Exception: {err}"))
        page.on("requestfailed", lambda req: print(f"Request Failed: {req.method} {req.url} - {req.failure.error_text if req.failure else ''}"))
        
        # Navigate to local tester served on port 8000
        print("Navigating to http://localhost:8000...")
        await page.goto("http://localhost:8000")
        
        # Verify page loaded
        await page.wait_for_selector("text=A2UI Local Tester")
        print("Page loaded successfully.")
        
        # Send greeting message to initiate agent greeting and intake form
        print("Sending initial greeting to agent...")
        await page.locator('#input').fill("hello")
        await page.locator('button:has-text("Send")').click()
        
        # Wait for agent greeting and intake form to render
        print("Waiting for intake form components...")
        await page.wait_for_selector('[id="/trip/start_location_input"]')
        await page.wait_for_selector('[id="/trip/end_location_input"]')
        await page.wait_for_selector('[id="/trip/start_time_input"]')
        
        # Verify checkbox functionality
        print("Testing address synchronization via 'Same as starting address' checkbox...")
        
        # 1. Fill start location
        print("Filling in start location...")
        await page.locator('[id="/trip/start_location_input"]').fill("130 West Paces Ferry Rd NW, Atlanta, GA 30305")
        
        # 2. Assert end location is initially empty
        end_val = await page.locator('[id="/trip/end_location_input"]').input_value()
        assert end_val == "", "End location should be empty initially"
        
        # 3. Check the same_as_start checkbox
        print("Checking 'Same as starting address' checkbox...")
        await page.locator('[id="/trip/same_as_start_checkbox"]').click()
        
        # 4. Assert end location is now filled with start location
        end_val = await page.locator('[id="/trip/end_location_input"]').input_value()
        assert end_val == "130 West Paces Ferry Rd NW, Atlanta, GA 30305", f"Expected synced address, got: {end_val}"
        print("Checkbox copy verified successfully!")
        
        # 5. Modify start location and assert end location is updated
        print("Modifying start location to check dynamic synchronization...")
        await page.locator('[id="/trip/start_location_input"]').fill("101 E Court Square, Decatur, GA 30030")
        end_val = await page.locator('[id="/trip/end_location_input"]').input_value()
        assert end_val == "101 E Court Square, Decatur, GA 30030", f"Expected dynamically updated address, got: {end_val}"
        print("Dynamic synchronization verified successfully!")
        
        # 6. Modify end location manually and assert checkbox is unchecked
        print("Modifying end location manually to check unchecking behavior...")
        await page.locator('[id="/trip/end_location_input"]').fill("2200 Avalon Blvd, Alpharetta, GA 30009")
        is_checked = await page.locator('[id="/trip/same_as_start_checkbox"]').is_checked()
        assert not is_checked, "Checkbox should be unchecked after manual edit of ending address"
        print("Manual override unchecking verified successfully!")
        
        # 7. Check the checkbox again to reset to same location for planning submission
        print("Re-checking checkbox to reset start and end locations...")
        await page.locator('[id="/trip/start_location_input"]').fill("130 West Paces Ferry Rd NW, Atlanta, GA 30305")
        await page.locator('[id="/trip/same_as_start_checkbox"]').click()
        
        print("Filling in start time...")
        # Since DateTimeInput timepicker is used, set the value directly in the element
        await page.locator('[id="/trip/start_time_input"]').fill("08:30")
        
        # Let client dataModel sync
        await asyncio.sleep(1)
        
        # Click the "Start Planning" button
        print("Clicking 'Start Planning'...")
        await page.locator('button:has-text("Start Planning")').click()
        
        # Wait for the agent response and rich UI rendering
        print("Waiting for route map and timeline dashboard (can take 10-20 seconds for API queries)...")
        # The schedule view rendering will create a WebFrameUrl directions map iframe
        map_iframe_locator = page.locator('iframe[src*="directions"]').first
        await map_iframe_locator.wait_for(state="attached", timeout=120000)
        print("Google Maps directions iframe rendered successfully!")
        
        # Verify dashboard title and text content
        await page.wait_for_selector("text=Optimized Route Schedule")
        await page.wait_for_selector("text=Workday Summary")
        await page.wait_for_selector("text=Total Serviced:")
        print("Summary stats and timeline elements validated successfully in the DOM.")
        
        # Remove height restriction and scroll to show all content for screenshot
        await page.evaluate('''() => {
            const chat = document.getElementById('chat');
            chat.style.height = 'auto';
            chat.style.overflow = 'visible';
        }''')
        
        # Wait for Google Maps to finish loading and rendering assets
        print("Waiting 10 seconds for Google Maps iframe to load and paint assets...")
        await asyncio.sleep(10)
        
        # Save screenshot of the page
        print(f"Taking screenshot of the page and saving to {screenshot_path}...")
        await page.screenshot(path=screenshot_path, full_page=True)
        print("E2E browser test completed successfully!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
