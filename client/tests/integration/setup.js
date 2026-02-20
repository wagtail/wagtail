const { mkdir, writeFile } = require('fs').promises;
const os = require('os');
const path = require('path');
const { chromium } = require('playwright');

const DIR = path.join(os.tmpdir(), 'jest_playwright_global_setup');

/**
 * Custom Playwright setup for Jest integration.
 */
module.exports = async () => {
  const browserServer = await chromium.launchServer();
  // store the browser server instance so we can teardown it later
  // this global is only available in the teardown but not in TestEnvironments
  global.__BROWSER_GLOBAL__ = browserServer;

  // Make sure this matches the origin defined in PlaywrightEnvironment.js.
  const testOrigin = process.env.TEST_ORIGIN ?? 'http://localhost:8000';

  // use the file system to expose the wsEndpoint for TestEnvironments
  await mkdir(DIR, { recursive: true });
  await writeFile(path.join(DIR, 'wsEndpoint'), browserServer.wsEndpoint());

  // Automatically log into the Wagtail admin and save authentication state.
  // Connect to the browser server to perform the login
  const browser = await chromium.connect(browserServer.wsEndpoint());
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(`${testOrigin}/admin/login/`);
  await page.fill('#id_username', 'admin');
  await page.fill('#id_password', 'changeme');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'load' }),
    page.keyboard.press('Enter'),
  ]);

  // Save the authentication state (cookies, localStorage, etc.)
  await context.storageState({ path: path.join(DIR, 'storageState.json') });

  await context.close();
  await browser.close();
};
