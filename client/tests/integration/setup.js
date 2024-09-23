const { mkdir, writeFile } = require('fs').promises;
const os = require('os');
const path = require('path');
const puppeteer = require('puppeteer');

const DIR = path.join(os.tmpdir(), 'jest_puppeteer_global_setup');

/**
 * Custom Puppeteer setup as documented on https://jestjs.io/docs/puppeteer.
 */
module.exports = async () => {
  const browser = await puppeteer.launch();
  // store the browser instance so we can teardown it later
  // this global is only available in the teardown but not in TestEnvironments
  global.__BROWSER_GLOBAL__ = browser;

  // Make sure this matches the origin defined in PuppeteerEnvironment.js.
  const testOrigin = process.env.TEST_ORIGIN ?? 'http://localhost:8000';

  // use the file system to expose the wsEndpoint for TestEnvironments
  await mkdir(DIR, { recursive: true });
  await writeFile(path.join(DIR, 'wsEndpoint'), browser.wsEndpoint());

  // Automatically log into the Wagtail admin.
  const page = await browser.newPage();
  await page.goto(`${testOrigin}/admin/login/`);
  await page.type('#id_username', 'admin');
  await page.type('#id_password', 'changeme');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'load' }),
    page.keyboard.press('Enter'),
  ]);
};
