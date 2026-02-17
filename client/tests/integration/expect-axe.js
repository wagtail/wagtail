const AxeBuilder = require('@axe-core/playwright').default;

/**
 * Helper function to run accessibility tests with axe-core.
 * @param {import('playwright').Page} page - Playwright page object
 * @param {Object} options - Options for axe testing
 * @param {string} options.exclude - CSS selector for elements to exclude
 * @param {string} options.include - CSS selector for elements to include
 * @returns {Promise<void>}
 * @see https://playwright.dev/docs/accessibility-testing
 */
async function expectToPassAxeTests(page, options = {}) {
  const builder = new AxeBuilder({ page });

  if (options.exclude) {
    builder.exclude(options.exclude);
  }

  if (options.include) {
    builder.include(options.include);
  }

  const results = await builder.analyze();

  if (results.violations.length > 0) {
    const violations = results.violations.map((violation) => {
      const nodes = violation.nodes.map(
        (node) => `  - ${node.html}\n    ${node.failureSummary}`,
      );
      return `${violation.id}: ${violation.description}\n${nodes.join('\n')}`;
    });
    throw new Error(
      `Accessibility violations found:\n\n${violations.join('\n\n')}`,
    );
  }
}

// Add custom matcher to Jest
expect.extend({
  async toPassAxeTests(page, options) {
    try {
      await expectToPassAxeTests(page, options);
      return {
        pass: true,
        message: () => 'Accessibility tests passed',
      };
    } catch (error) {
      return {
        pass: false,
        message: () => error.message,
      };
    }
  },
});

module.exports = { expectToPassAxeTests };
