const { chromium } = require('playwright');

(async () => {
  console.log('Starting E2E Verification with Playwright...');
  let browser;
  try {
    browser = await chromium.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-web-security',
        '--disable-features=IsolateOrigins,site-per-process'
      ]
    });
    const page = await browser.newPage();

    // Listen for browser console logs and errors
    page.on('console', msg => console.log(`BROWSER LOG [${msg.type()}]:`, msg.text()));
    page.on('pageerror', err => console.error('BROWSER ERROR:', err));

    // 1. Navigate to the local frontend server
    const url = 'http://localhost:5173/?app=phoneplan';
    console.log(`Navigating to ${url}...`);
    await page.goto(url);

    // 2. Wait for the app to load (shell element)
    try {
      await page.waitForSelector('body', { timeout: 10000 });
      console.log('Page body loaded.');
      await page.waitForSelector('a2ui-shell', { timeout: 15000 });
      console.log('App loaded (found <a2ui-shell>)');
    } catch (e) {
      console.error('Failed to find app components. Content:', await page.content());
      throw e;
    }

    // 3. Send initial message
    console.log('Typing initial message...');
    const input = page.locator('input[type="text"]').first();
    await input.waitFor({ state: 'visible', timeout: 15000 });
    await input.fill('I need a plan with about 5GB of data and I want the new Pixel 9.');
    await input.press('Enter');
    console.log('Message sent. Waiting for response...');

    // 4. Verify Visual Components (e.g., A2UI Buttons for plans)
    try {
      const basicSaverBtn = page.getByText('Basic Saver');
      await basicSaverBtn.waitFor({ state: 'visible', timeout: 60000 });
      console.log('✅ Plan rendering verified (Basic Saver button found).');
    } catch (e) {
      console.error('❌ Expected A2UI components did not appear.');
      console.log('Current page content:', await page.content());
      process.exit(1);
    }

    console.log('✅ E2E Browser Test Passed!');

  } catch (error) {
    console.error('❌ Test Failed:', error);
    process.exit(1);
  } finally {
    if (browser) await browser.close();
  }
})();
