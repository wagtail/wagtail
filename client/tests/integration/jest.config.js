module.exports = {
  globalSetup: './setup.js',
  globalTeardown: './teardown.js',
  testEnvironment: './PuppeteerEnvironment.js',
  setupFilesAfterEnv: ['expect-puppeteer', '@wordpress/jest-puppeteer-axe'],
};
