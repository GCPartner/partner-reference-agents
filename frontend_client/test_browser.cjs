const { chromium } = require('playwright');
(async () => {
  try {
    const browser = await chromium.launch({
      headless: false,
      args: ['--remote-debugging-port=9222']
    });
    console.log("Browser launched successfully on port 9222");
    await new Promise(r => setTimeout(r, 5000));
    await browser.close();
  } catch (e) {
    console.error("Browser launch failed:", e);
  }
})();
