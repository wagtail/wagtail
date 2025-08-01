# Accessing the editor programmatically

Wagtail's editor is built with various JavaScript components that can be interacted with programmatically. This document provides an overview of how to access and extend the editor's functionality.

## The editor's `<form>` element

The editor's main `<form>` element can be queried using the `data-edit-form` attribute. This is useful for attaching event listeners or manipulating the form programmatically, as well as getting the form's `FormData` representation.

```javascript
const editForm = document.querySelector('form[data-edit-form]');
const data = new FormData(editForm);
```

## The preview panel

The preview panel is powered by the [`PreviewController`](controller:PreviewController) and its instance can be accessed using the [`wagtail.app.queryController`](client:classes/includes_initStimulus.WagtailApplication#querycontroller) function. The `PreviewController` provides methods to control the preview, such as extracting the previewed content and running content checks. Refer to the `PreviewController` documentation for more details.

```javascript
const previewController = window.wagtail.app.queryController('w-preview');
const content = await previewController?.extractContent();
await previewController?.runContentChecks();
```

## Example: generating meta description

Extracting the previewed content using the `PreviewController` can be useful for different use cases. One example is generating a meta description for the page using a Large Language Model (LLM). The following example demonstrates a [custom Stimulus controller](extending_client_side_stimulus) that uses an LLM from the browser's [Summarizer API](https://developer.mozilla.org/en-US/docs/Web/API/Summarizer) to generate the page's meta description.

```javascript
/* js/summarize.js */

class SummarizeController extends window.StimulusModule.Controller {
  static targets = ['suggest'];

  static values = {
    input: { default: '', type: String },
  };

  /** Only load the controller if the browser supports the Summarizer API. */
  static get shouldLoad() {
    return 'Summarizer' in window;
  }

  /** The previewed content's language. */
  contentLanguage = document.documentElement.lang || 'en';
  /** A cached Summarizer instance Promise to avoid recreating it unnecessarily. */
  #summarizer = null;

  /** Promise of a browser Summarizer instance. */
  get summarizer() {
    if (this.#summarizer) return this.#summarizer; // Return from cache
    this.#summarizer = Summarizer.create({
      // Change the Summarizer's configuration as needed
      sharedContext: `A summary of a webpage's content, suitable for use as a meta description.`,
      type: 'teaser',
      length: 'short',
      format: 'plain-text',
      expectedInputLanguages: [this.contentLanguage],
      outputLanguage: document.documentElement.lang,
    });
    return this.#summarizer;
  }

  connect() {
    this.input = this.element.querySelector(this.inputValue);
    this.renderFurniture();
  }

  renderFurniture() {
    const prefix = this.element.closest('[id]').id;
    const buttonId = `${prefix}-generate`;
    const button = /* html */ `
      <button
        id="${buttonId}"
        type="button"
        data-summarize-target="suggest"
        data-action="summarize#generate"
        class="button"
      >
        Generate suggestions
      </button>
    `;
    this.element.insertAdjacentHTML('beforeend', button);

    this.outputArea = document.createElement('div');
    this.element.append(this.outputArea);
  }

  renderSuggestion(suggestion) {
    const template = document.createElement('template');
    template.innerHTML = /* html */ `
      <div>
        <output for="${this.suggestTarget.id}">${suggestion}</output>
        <button class="button button-small" type="button" data-action="summarize#useSuggestion">Use</button>
      </div>
    `;
    this.outputArea.append(template.content.firstElementChild);
  }

  useSuggestion(event) {
    this.input.value = event.target.previousElementSibling.textContent;
  }

  async summarize(text) {
    const summarizer = await this.summarizer;
    return summarizer.summarize(text);
  }

  async getPageContent() {
    const previewController = window.wagtail.app.queryController('w-preview');
    const { innerText, lang } = await previewController.extractContent();
    this.contentLanguage = lang;
    return innerText;
  }

  async generate() {
    this.outputArea.innerHTML = '';
    this.suggestTarget.textContent = 'Generating…';
    this.suggestTarget.disabled = true;

    const text = await this.getPageContent();
    await Promise.allSettled(
      [...Array(3).keys()].map(() =>
        this.summarize(text)
          .then((output) => this.renderSuggestion(output))
          .catch((error) => {
            console.error('Error generating suggestion:', error);
          }),
      ),
    );

    this.suggestTarget.disabled = false;
    this.suggestTarget.textContent = 'Generate suggestions';
  }
}

window.wagtail.app.register('summarize', SummarizeController);
```

The JavaScript file can be loaded to the editor using the `insert_editor_js` hook and attached to the `Page`'s `FieldPanel` for the `search_description` field:

```python
# myapp/wagtail_hooks.py
from django.templatetags.static import static
from django.utils.html import format_html_join
from wagtail import hooks
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page


@hooks.register("insert_editor_js")
def editor_js():
    js_files = ["js/summarize.js"]
    return format_html_join(
        "\n",
        '<script src="{}"></script>',
        ((static(filename),) for filename in js_files),
    )

# Replace the default `FieldPanel` for `search_description`
# with a custom one that uses the `summarize` controller.
Page.promote_panels[0].args[0][-1] = FieldPanel(
    "search_description",
    attrs={
        "data-controller": "summarize",
        "data-summarize-input-value": "[name='search_description']",
    },
)
```
