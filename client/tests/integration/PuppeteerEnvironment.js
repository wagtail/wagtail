const { readFile } = require('fs').promises;
const os = require('os');
const path = require('path');
const puppeteer = require('puppeteer');
const NodeEnvironment = require('jest-environment-node');

const DIR = path.join(os.tmpdir(), 'jest_puppeteer_global_setup');

/**
 * Custom Puppeteer environment as documented on https://jestjs.io/docs/puppeteer.
 * We don’t use jest-puppeteer because it’s unreliable.
 */
class PuppeteerEnvironment extends NodeEnvironment {
  async setup() {
    await super.setup();
    // get the wsEndpoint
    const wsEndpoint = await readFile(path.join(DIR, 'wsEndpoint'), 'utf8');
    if (!wsEndpoint) {
      throw new Error('wsEndpoint not found');
    }

    this.global.TEST_ORIGIN =
      process.env.TEST_ORIGIN ?? 'http://localhost:8000';

    // connect to puppeteer
    this.global.browser = await puppeteer.connect({
      browserWSEndpoint: wsEndpoint,
      defaultViewport: {
        width: 1024,
        height: 768,
      },
    });

    this.global.page = await this.global.browser.newPage();
  }

  async teardown() {
    await this.global.page.close();

    await super.teardown();
  }

  getVmContext() {
    return super.getVmContext();
  }
}

module.exports = PuppeteerEnvironment;
