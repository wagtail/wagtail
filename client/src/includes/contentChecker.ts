import axe, {
  AxeResults,
  Check,
  ContextObject,
  CrossTreeSelector,
  NodeResult,
  Result,
  RunOptions,
  Spec,
} from 'axe-core';

const toSelector = (str: string | string[] | CrossTreeSelector[]) =>
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
 * `wagtail.admin.userbar.ContentCheckerItem.get_axe_configuration()`.
 */
export interface ErrorMessage {
  error_name: string;
  help_text: string;
}

export interface ErrorMessages {
  [key: string]: string | ErrorMessage;
}

export interface WagtailAxeConfiguration {
  context: ContextObject;
  options: RunOptions;
  messages: ErrorMessages;
  spec: Spec;
}

/**
 * Resolve the display name and help text for a violation, preferring
 * Wagtail's custom messages over axe defaults.
 */
export const getViolationMessage = (
  violation: { id: string; help: string; description: string },
  messages: ErrorMessages,
): { name: string; helpText: string } => {
  const msg = messages[violation.id];
  const name =
    (typeof msg === 'string' ? msg : msg?.error_name) || violation.help;
  const helpText =
    (typeof msg !== 'string' && msg?.help_text) || violation.description;
  return { name, helpText };
};

/**
 * Get the Axe configuration from the page.
 */
export const getAxeConfiguration = (
  container: ShadowRoot | HTMLElement | null,
): WagtailAxeConfiguration | null => {
  const script = container?.querySelector<HTMLScriptElement>(
    '#checker-axe-configuration',
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
 * contains poor quality text like file extensions or underscores.
 * The rule will be added via the Axe.configure() API.
 * @see https://github.com/dequelabs/axe-core/blob/master/doc/API.md#api-name-axeconfigure
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
 * Checks whether a meta description tag is present but empty.
 */
export const checkEmptyMetaDescription = () => {
  const elt = document.querySelector<HTMLMetaElement>(
    'meta[name="description"][content]',
  );
  return !elt || elt.content.trim().length > 0;
};

/**
 * Defines custom Axe rules, mapping each check to its corresponding JavaScript function.
 * This object holds the custom checks that will be added to the Axe configuration.
 */
export const customChecks = {
  'check-image-alt-text': checkImageAltText,
  'check-empty-meta-description': checkEmptyMetaDescription,
};

/**
 * Registers a custom check to be used by Axe.
 * @param id - The ID of the check
 * @param evaluate - The evaluation function for the check
 */
export const registerCustomCheck = (
  id: string,
  evaluate: Check['evaluate'],
) => {
  customChecks[id] = evaluate;
  return customChecks;
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

interface CheckerReport {
  results: AxeResults;
  issueCount: number;
}

/**
 * Get content checker results from Axe based on the configurable custom context and options.
 * Before calling this function, ensure that Axe has been configured with
 * axe.configure() using the config's `spec`, along with any custom checks.
 */
export const getCheckerReport = async (
  config: WagtailAxeConfiguration,
): Promise<CheckerReport> => {
  // Run Axe based on the context and options defined in Python.
  const results = await axe.run(config.context, config.options);
  const issueCount = results.violations.reduce(
    (sum, violation) => sum + violation.nodes.length,
    0,
  );

  if (issueCount > 0) {
    // Help developers potentially troubleshooting userbar check results.
    // eslint-disable-next-line no-console
    console.error('axe.run results', results.violations);
  }

  return {
    results,
    issueCount,
  };
};

/**
 * Render content checker results based on template elements.
 */
export const renderCheckerResults = (
  container: HTMLElement,
  results: AxeResults,
  config: WagtailAxeConfiguration,
  checkerRowTemplate: HTMLTemplateElement,
  onClickSelector: (selectorName: string, event: MouseEvent) => void,
) => {
  // Reset contents ahead of rendering new results.
  container.innerHTML = '';

  if (results.violations.length) {
    const sortedViolations = sortAxeViolations(results.violations);
    let nodeCounter = 0;
    sortedViolations.forEach((violation) => {
      violation.nodes.forEach((node) => {
        container.appendChild(checkerRowTemplate.content.cloneNode(true));

        const row = container.querySelectorAll<HTMLDivElement>(
          '[data-content-checker-row]',
        )[nodeCounter];
        nodeCounter += 1;

        const errorName = row.querySelector(
          '[data-content-checker-name]',
        ) as HTMLSpanElement;
        const errorHelp = row.querySelector(
          '[data-content-checker-help]',
        ) as HTMLDivElement;
        errorName.id = `w-content-checker__name-${nodeCounter}`;

        const { name, helpText } = getViolationMessage(
          violation,
          config.messages,
        );
        errorName.textContent = name;
        errorHelp.textContent = helpText;

        // Special-case when displaying results within the admin interface.
        const isInCMS = node.target[0] === '#w-preview-iframe';
        const selectorName = toSelector(
          node.target.filter((target) => target !== '#w-preview-iframe'),
        );

        const selector = row.querySelector(
          '[data-content-checker-selector]',
        ) as HTMLButtonElement;
        selector.setAttribute('aria-describedby', errorName.id);
        selector.addEventListener(
          'click',
          onClickSelector.bind(null, selectorName),
        );

        // Display the selector text in the CMS,
        // as a workaround until we highlight errors within the preview panel.
        if (isInCMS) {
          const selectorText = selector.querySelector(
            '[data-content-checker-selector-text]',
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
