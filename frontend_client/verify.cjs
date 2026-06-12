const { chromium } = require('playwright');

(async () => {
  // Launch browser
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  console.log("Navigating to local vite dev server...");
  await page.goto('http://localhost:5174/?app=phoneplan');

  // 1. Wait for input and send "Hello"
  await page.waitForSelector('input#body');
  await page.fill('input#body', 'I need a plan with about 5GB of data and I want the new Pixel 9.');
  await page.click('button[type="submit"]');

  console.log("Waiting for A2UI components to render...");
  // 2. Wait for A2UI components (buttons representing plans) to appear
  await page.waitForSelector('a2ui-surface button', { timeout: 30000 });

  // Check if the plan buttons appeared
  const buttonTexts = await page.$$eval('a2ui-surface button', buttons => buttons.map(b => b.textContent));
  console.log("Plan Buttons Found:", buttonTexts);

  if (buttonTexts.some(text => text.includes("Select Basic Saver"))) {
    console.log("SUCCESS: A2UI Buttons rendered correctly.");
  } else {
    console.error("FAILURE: Expected A2UI plan buttons were not found.");
    process.exit(1);
  }

  await browser.close();
})();
