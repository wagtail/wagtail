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
interface WagtailAxeConfiguration {
  context: ElementContext;
  options: RunOptions;
  messages: Record<string, string>;
  custom: Spec;
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
 * Custom rule for checking image alt text. Will be added via the Axe.configure() API
 * https://github.com/dequelabs/axe-core/blob/master/doc/API.md#api-name-axeconfigure
 */
export const checkImageAltText = (node: Element) => {
  const imageFileExtensions = [
    'apng',
    'avif',
    'gif',
    'jpg',
    'jpeg',
    'jfif',
    'pjpeg',
    'pjp',
    'png',
    'svg',
    'tif',
    'webp',
  ];
  const imageURLs = ['http://', 'https://', 'www.'];
  const altTextAntipatterns = new RegExp(
    `\\.(${imageFileExtensions.join('|')})|(${imageURLs.join('|')})`,
    'i',
  );

  const image = node as HTMLImageElement;
  const altText = image.getAttribute('alt') || '';

  const hasBadAltText = altTextAntipatterns.test(altText);
  return !hasBadAltText;
};

/**
 * Defines custom Axe rules, mapping each check to its corresponding JavaScript function.
 */
const customChecks = {
  'check-image-alt-text': checkImageAltText,
  // Add other custom checks here
};

/**
 * Configures custom Axe rules.
 */
const addCustomChecks = (customConfig: Spec): Spec => {
  const modifiedChecks = customConfig?.checks?.map((check) => {
    if (customChecks[check.id]) {
      return {
        ...check,
        evaluate: customChecks[check.id],
      };
    }
    return check;
  });

  return {
    ...customConfig,
    checks: modifiedChecks,
  };
};

interface A11yReport {
  results: AxeResults;
  a11yErrorsNumber: number;
}

/**
 * Get accessibility testing results from Axe based on the configurable custom checks, context, and options.
 */
export const getA11yReport = async (
  config: WagtailAxeConfiguration,
): Promise<A11yReport> => {
  // Add custom checks for Axe if any. 'check-image-alt-text' is enabled by default
  if (config.custom && config.custom.checks && config.custom.rules) {
    axe.configure(addCustomChecks(config.custom));
  }

  // Initialise Axe based on the context (whole page body by default) and options ('button-name', empty-heading', 'empty-table-header', 'frame-title', 'heading-order', 'input-button-name', 'link-name', 'p-as-heading', and a custom 'alt-text-quality' rules by default)
  const results = await axe.run(config.context, config.options);

  const a11yErrorsNumber = results.violations.reduce(
    (sum, violation) => sum + violation.nodes.length,
    0,
  );

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
  a11ySelectorTemplate: HTMLTemplateElement,
  onClickSelector: (selectorName: string, event: MouseEvent) => void,
) => {
  // Reset contents ahead of rendering new results.
  // eslint-disable-next-line no-param-reassign
  container.innerHTML = '';

  if (results.violations.length) {
    const sortedViolations = sortAxeViolations(results.violations);
    sortedViolations.forEach((violation, violationIndex) => {
      container.appendChild(a11yRowTemplate.content.cloneNode(true));
      const currentA11yRow = container.querySelectorAll<HTMLDivElement>(
        '[data-a11y-result-row]',
      )[violationIndex];

      const a11yErrorName = currentA11yRow.querySelector(
        '[data-a11y-result-name]',
      ) as HTMLSpanElement;
      a11yErrorName.id = `w-a11y-result__name-${violationIndex}`;
      // Display custom error messages supplied by Wagtail if available,
      // fallback to default error message from Axe
      a11yErrorName.textContent =
        config.messages[violation.id] || violation.help;
      const a11yErrorCount = currentA11yRow.querySelector(
        '[data-a11y-result-count]',
      ) as HTMLSpanElement;
      a11yErrorCount.textContent = `${violation.nodes.length}`;

      const a11yErrorContainer = currentA11yRow.querySelector(
        '[data-a11y-result-container]',
      ) as HTMLDivElement;

      violation.nodes.forEach((node, nodeIndex) => {
        a11yErrorContainer.appendChild(
          a11ySelectorTemplate.content.cloneNode(true),
        );
        const currentA11ySelector =
          a11yErrorContainer.querySelectorAll<HTMLButtonElement>(
            '[data-a11y-result-selector]',
          )[nodeIndex];

        currentA11ySelector.setAttribute('aria-describedby', a11yErrorName.id);
        const currentA11ySelectorText = currentA11ySelector.querySelector(
          '[data-a11y-result-selector-text]',
        ) as HTMLSpanElement;
        // Special-case when displaying accessibility results within the admin interface.
        const selectorName = toSelector(
          node.target[0] === '#preview-iframe'
            ? node.target[1]
            : node.target[0],
        );
        // Remove unnecessary details before displaying selectors to the user
        currentA11ySelectorText.textContent = selectorName.replace(
          /\[data-block-key="\w{5}"\]/,
          '',
        );
        currentA11ySelector.addEventListener(
          'click',
          onClickSelector.bind(null, selectorName),
        );
      });
    });
  }
};
