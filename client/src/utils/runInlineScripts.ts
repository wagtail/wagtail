/**
 * Runs any inline scripts contained within the given DOM element or fragment.
 */
const runScript = (script: HTMLScriptElement) => {
  if (!script.type || script.type === 'application/javascript') {
    const newScript = document.createElement('script');
    Array.from(script.attributes).forEach((key) =>
      newScript.setAttribute(key.nodeName, key.nodeValue || ''),
    );
    newScript.text = script.text;
    script.replaceWith(newScript);
  }
};

/**
 * Finds and runs any inline scripts contained within the given DOM element or fragment.
 */
const runInlineScripts = (element: HTMLElement | DocumentFragment) => {
  const selector = 'script:not([src])';
  if (element instanceof HTMLElement && element.matches(selector)) {
    runScript(element as HTMLScriptElement);
  } else {
    const scripts = element.querySelectorAll(
      selector,
    ) as NodeListOf<HTMLScriptElement>;
    scripts.forEach(runScript);
  }
};

export { runInlineScripts };
