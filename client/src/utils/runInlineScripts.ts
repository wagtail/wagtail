/**
 * Runs any inline scripts contained within the given DOM element or fragment.
 */
const runInlineScripts = (element: HTMLElement | DocumentFragment) => {
  const scripts = element.querySelectorAll(
    'script:not([src])',
  ) as NodeListOf<HTMLScriptElement>;
  scripts.forEach((script) => {
    if (!script.type || script.type === 'application/javascript') {
      const newScript = document.createElement('script');
      Array.from(script.attributes).forEach((key) =>
        newScript.setAttribute(key.nodeName, key.nodeValue || ''),
      );
      newScript.text = script.text;
      script.replaceWith(newScript);
    }
  });
};

export { runInlineScripts };
