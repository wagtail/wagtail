module.exports = {
  globalSetup: './setup.js',
  globalTeardown: './teardown.js',
  testEnvironment: './PlaywrightEnvironment.js',
  setupFilesAfterEnv: ['./expect-axe.js'],
};
