const puppeteer = require('puppeteer-core');
const path = require('path');

const SCREENSHOT_DIR = path.resolve(process.argv[2] || 'screenshots');

async function main() {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();

  // Desktop viewport
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForSelector('header');
  await sleep(2000); // Let React render

  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01-landing.png'), fullPage: false });
  console.log('1. Landing page captured');

  // Click "Load Demo Scenario" button
  const demoBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    return buttons.find(b => b.textContent.includes('Load Demo') || b.textContent.includes('डेमो'));
  });

  if (demoBtn) {
    await demoBtn.click();
    console.log('2. Demo button clicked');
    
    // Wait for the demo to progress through steps
    await sleep(6000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02-demo-optimize.png'), fullPage: false });
    console.log('3. Optimization results captured');

    // Wait for stress test
    await sleep(5000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03-demo-stress.png'), fullPage: false });
    console.log('4. Stress test captured');

    // Wait for completion
    await sleep(5000);
    
    // Scroll down to see all results
    await page.evaluate(() => window.scrollTo(0, 600));
    await sleep(500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04-kpi-cards.png'), fullPage: false });
    console.log('5. KPI cards captured');

    await page.evaluate(() => window.scrollTo(0, 1200));
    await sleep(500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05-comparison.png'), fullPage: false });
    console.log('6. Comparison view captured');

    await page.evaluate(() => window.scrollTo(0, 2000));
    await sleep(500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06-stress-test.png'), fullPage: false });
    console.log('7. Stress test view captured');

    // Full page
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07-fullpage.png'), fullPage: true });
    console.log('8. Full page captured');
  }

  // Mobile viewport
  await page.setViewport({ width: 390, height: 844 });
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
  await sleep(2000);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08-mobile.png'), fullPage: false });
  console.log('9. Mobile view captured');

  await browser.close();
  console.log('Done!');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

main().catch(e => { console.error(e); process.exit(1); });
