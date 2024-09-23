import axe, {
  AxeResults,
  ElementContext,
  NodeResult,
  Result,
  RunOptions,
  Spec,
} from 'axe-core';

const toSelector = (str: string | string[]) =>
  Array.isArray(str) ? str.join(' ') : str;

const sortAxeNodes = (nodeResultA?: NodeResult, nodeResultB?: NodeResult) => {
  if (!nodeResultA || !nodeResultB) return 0;
  const nodeA = document.querySelector<HTMLElement>(
    toSelector(nodeResultA.target[0]),
  );
  const nodeB = document.querySelector<HTMLElement>(
    toSelector(nodeResultB.target[0]),
  );
  if (!nodeA || !nodeB) return 0;
  // Method works with bitwise https://developer.mozilla.org/en-US/docs/Web/API/Node/compareDocumentPosition
  // eslint-disable-next-line no-bitwise
  return nodeA.compareDocumentPosition(nodeB) & Node.DOCUMENT_POSITION_PRECEDING
    ? 1
    : -1;
};

/**
 * Sort Axe violations by position of the violation’s first node in the DOM.
 */
export const sortAxeViolations = (violations: Result[]) =>
  violations.sort((violationA, violationB) => {
    const earliestNodeA = violationA.nodes.sort(sortAxeNodes)[0];
    const earliestNodeB = violationB.nodes.sort(sortAxeNodes)[0];
    return sortAxeNodes(earliestNodeA, earliestNodeB);
  });

/**
 * Wagtail's Axe configuration object. This should reflect what's returned by
 * `wagtail.admin.userbar.AccessibilityItem.get_axe_configuration()`.
 */

interface ErrorMessage {
  error_name: string;
  help_text: string;
}
export interface WagtailAxeConfiguration {
  context: ElementContext;
  options: RunOptions;
  messages: Record<string, ErrorMessage>;
  spec: Spec;
}

/**
 * Get the Axe configuration from the page.
 */
export const getAxeConfiguration = (
  container: ShadowRoot | HTMLElement | null,
): WagtailAxeConfiguration | null => {
  const script = container?.querySelector<HTMLScriptElement>(
    '#accessibility-axe-configuration',
  );

  if (!script || !script.textContent) return null;

  try {
    return JSON.parse(script.textContent);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Error loading Axe config');
    // eslint-disable-next-line no-console
    console.error(err);
  }

  // Skip initialization of Axe if config fails to load
  return null;
};

/**
 * Custom rule for checking image alt text. This rule checks if the alt text for images
 * contains poor quality text like file extensions or undescores.
 * The rule will be added via the Axe.configure() API.
 * https://github.com/dequelabs/axe-core/blob/master/doc/API.md#api-name-axeconfigure
 */
export const checkImageAltText = (
  node: HTMLImageElement,
  options: { pattern: string },
) => {
  const altTextAntipatterns = new RegExp(options.pattern, 'i');
  const altText = node.getAttribute('alt') || '';

  const hasBadAltText = altTextAntipatterns.test(altText);
  return !hasBadAltText;
};

/**
 * Defines custom Axe rules, mapping each check to its corresponding JavaScript function.
 * This object holds the custom checks that will be added to the Axe configuration.
 */
export const customChecks = {
  'check-image-alt-text': checkImageAltText,
  // Add other custom checks here
};

/**
 * Configures custom Axe rules by integrating the custom checks with their corresponding
 * JavaScript functions. It modifies the provided configuration to include these checks.
 */
export const addCustomChecks = (spec: Spec): Spec => {
  const modifiedChecks = spec?.checks?.map((check) => {
    if (customChecks[check.id]) {
      return {
        ...check,
        evaluate: customChecks[check.id],
      };
    }
    return check;
  });
  return {
    ...spec,
    checks: modifiedChecks,
  };
};

interface A11yReport {
  results: AxeResults;
  a11yErrorsNumber: number;
}

/**
 * Get accessibility testing results from Axe based on the configurable custom spec, context, and options.
 * It integrates custom rules into the Axe configuration before running the tests.
 */
export const getA11yReport = async (
  config: WagtailAxeConfiguration,
): Promise<A11yReport> => {
  axe.configure(addCustomChecks(config.spec));
  // Initialise Axe based on the context and options defined in Python.
  const results = await axe.run(config.context, config.options);
  const a11yErrorsNumber = results.violations.reduce(
    (sum, violation) => sum + violation.nodes.length,
    0,
  );

  if (a11yErrorsNumber > 0) {
    // Help developers potentially troubleshooting userbar check results.
    // eslint-disable-next-line no-console
    console.error('axe.run results', results.violations);
  }

  return {
    results,
    a11yErrorsNumber,
  };
};

/**
 * Render A11y results based on template elements.
 */
export const renderA11yResults = (
  container: HTMLElement,
  results: AxeResults,
  config: WagtailAxeConfiguration,
  a11yRowTemplate: HTMLTemplateElement,
  onClickSelector: (selectorName: string, event: MouseEvent) => void,
) => {
  // Reset contents ahead of rendering new results.
  // eslint-disable-next-line no-param-reassign
  container.innerHTML = '';

  if (results.violations.length) {
    const sortedViolations = sortAxeViolations(results.violations);
    let nodeCounter = 0;
    sortedViolations.forEach((violation) => {
      violation.nodes.forEach((node) => {
        container.appendChild(a11yRowTemplate.content.cloneNode(true));

        const currentA11yRow = container.querySelectorAll<HTMLDivElement>(
          '[data-a11y-result-row]',
        )[nodeCounter];
        nodeCounter += 1;

        const a11yErrorName = currentA11yRow.querySelector(
          '[data-a11y-result-name]',
        ) as HTMLSpanElement;
        const a11yErrorHelp = currentA11yRow.querySelector(
          '[data-a11y-result-help]',
        ) as HTMLDivElement;
        a11yErrorName.id = `w-a11y-result__name-${nodeCounter}`;

        // Display custom error messages supplied by Wagtail if available,
        // fallback to default error message from Axe
        const messages = config.messages[violation.id];

        const name =
          (typeof messages === 'string' ? messages : messages?.error_name) ||
          violation.help;
        a11yErrorName.textContent = name;
        a11yErrorHelp.textContent =
          messages?.help_text || violation.description;

        // Special-case when displaying accessibility results within the admin interface.
        const isInCMS = node.target[0] === '#w-preview-iframe';
        const selectorName = toSelector(
          isInCMS ? node.target[1] : node.target[0],
        );

        const a11ySelector = currentA11yRow.querySelector(
          '[data-a11y-result-selector]',
        ) as HTMLButtonElement;
        a11ySelector.setAttribute('aria-describedby', a11yErrorName.id);
        a11ySelector.addEventListener(
          'click',
          onClickSelector.bind(null, selectorName),
        );

        // Display the selector text in the CMS,
        // as a workaround until we highlight errors within the preview panel.
        if (isInCMS) {
          const selectorText = a11ySelector.querySelector(
            '[data-a11y-result-selector-text]',
          ) as HTMLSpanElement;
          // Remove unnecessary details before displaying selectors to the user
          selectorText.textContent = selectorName.replace(
            /\[data-block-key="\w{5}"\]/,
            '',
          );
        }
      });
    });
  }
};
