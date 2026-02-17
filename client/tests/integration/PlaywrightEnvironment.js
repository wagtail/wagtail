const { readFile } = require('fs').promises;
const os = require('os');
const path = require('path');
const NodeEnvironment = require('jest-environment-node').TestEnvironment;
const { chromium } = require('playwright');

const DIR = path.join(os.tmpdir(), 'jest_playwright_global_setup');

/**
 * Custom Playwright environment for Jest integration.
 */
class PlaywrightEnvironment extends NodeEnvironment {
  async setup() {
    await super.setup();
    // get the wsEndpoint
    const wsEndpoint = await readFile(path.join(DIR, 'wsEndpoint'), 'utf8');
    if (!wsEndpoint) {
      throw new Error('wsEndpoint not found');
    }

    this.global.TEST_ORIGIN =
      process.env.TEST_ORIGIN ?? 'http://localhost:8000';

    // connect to playwright browser
    this.global.browser = await chromium.connect(wsEndpoint);

    // Create a new context and page with saved authentication state
    const storageStatePath = path.join(DIR, 'storageState.json');
    this.global.context = await this.global.browser.newContext({
      viewport: {
        width: 1024,
        height: 768,
      },
      storageState: storageStatePath,
    });

    this.global.page = await this.global.context.newPage();
  }

  async teardown() {
    await this.global.page?.close();
    await this.global.context?.close();
    await this.global.browser?.close();

    await super.teardown();
  }

  getVmContext() {
    return super.getVmContext();
  }
}

module.exports = PlaywrightEnvironment;
