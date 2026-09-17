const JS_TYPES = new Set([
  '',
  'text/javascript',
  'application/javascript',
  'text/ecmascript',
  'application/ecmascript',
  'module',
]);

const runScripts = (element) => {
  const scripts = element.matches?.('script')
    ? [element]
    : Array.from(element.querySelectorAll?.('script') || []);

  scripts.forEach((script) => {
    const type = (script.type || '').toLowerCase();
    if (JS_TYPES.has(type)) {
      const newScript = document.createElement('script');
      Array.from(script.attributes).forEach((attr) =>
        newScript.setAttribute(attr.nodeName, attr.nodeValue || ''),
      );
      newScript.text = script.text;
      script.replaceWith(newScript);
    }
  });
};

/**
 * Usage of this class directly is deprecated for admin core code use.
 * Class still needs to be in place for legacy support (see `window.buildExpandingFormset`)
 * and it's being extended by InlinePanel & MultipleChooserPanel.
 *
 * @deprecated - Will be removed in a future release once fully migrated to Stimulus.
 * @see `client/src/controllers/FormsetController.ts` for the future (WIP) implementation.
 */
export class ExpandingFormset {
  constructor(prefix, opts = {}, initControls = true) {
    this.opts = opts;
    const addButton = document.getElementById(prefix + '-ADD');
    this.formContainer = document.getElementById(prefix + '-FORMS');
    this.totalFormsInput = document.getElementById(prefix + '-TOTAL_FORMS');

    const emptyFormElement = document.getElementById(
      prefix + '-EMPTY_FORM_TEMPLATE',
    );

    this.emptyFormTemplate = emptyFormElement.innerHTML;

    if (initControls) {
      if (opts.onInit) {
        for (let i = 0; i < this.formCount; i += 1) {
          opts.onInit(i);
        }
      }

      addButton?.addEventListener('click', () => {
        this.addForm();
      });
    }
  }

  get formCount() {
    return parseInt(this.totalFormsInput.value, 10);
  }

  /**
   * @param {object?} opts
   * @param {boolean?} opts.runCallbacks - (default: true) - if false, the onAdd and onInit callbacks will not be run
   */
  addForm(opts = {}) {
    const formIndex = this.formCount;
    const newFormHtml = this.emptyFormTemplate.replace(
      /__prefix__(.*?('|"|\\u0022))/g,
      formIndex + '$1',
    );

    const template = document.createElement('template');
    template.innerHTML = newFormHtml;
    const fragment = template.content;
    const insertedElements = Array.from(fragment.children);

    this.formContainer.appendChild(fragment);
    insertedElements.forEach((element) => {
      runScripts(element);
    });

    this.totalFormsInput.value = this.formCount + 1;

    if (!('runCallbacks' in opts) || opts.runCallbacks) {
      if (this.opts.onAdd) this.opts.onAdd(formIndex);
      if (this.opts.onInit) this.opts.onInit(formIndex);
    }
  }
}
