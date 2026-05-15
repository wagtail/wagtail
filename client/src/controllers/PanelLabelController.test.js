import { Application } from '@hotwired/stimulus';
import { PanelLabelController } from './PanelLabelController';

const flushAsync = () =>
  new Promise((resolve) => {
    setTimeout(resolve, 0);
  });

describe('PanelLabelController', () => {
  let application;

  const setEditHandler = (fieldValues) => {
    window.wagtail = window.wagtail || {};
    window.wagtail.editHandler = {
      getPanelByName(name) {
        if (!(name in fieldValues)) return null;
        return {
          getBoundWidget() {
            return {
              getTextLabel() {
                return fieldValues[name];
              },
            };
          },
        };
      },
    };
  };

  const setHtml = (formatValue, headingText, fields) => {
    document.body.innerHTML = `
      <section data-controller="w-panel-label" data-w-panel-label-format-value="${formatValue}">
        <h2><button data-panel-toggle></button><span data-panel-heading-text>${headingText}</span></h2>
        ${fields}
      </section>
    `;
  };

  const togglePanel = () => {
    document
      .querySelector('[data-panel-toggle]')
      .dispatchEvent(
        new CustomEvent('wagtail:panel-toggle', { bubbles: true }),
      );
  };

  const start = () => {
    application = Application.start();
    application.register('w-panel-label', PanelLabelController);
  };

  afterEach(() => {
    application?.stop();
    delete window.wagtail;
  });

  test('setCollapsedLabelText() renders the format from bound widget labels', async () => {
    setEditHandler({ first_name: 'Ada', last_name: 'Lovelace' });
    setHtml(
      '{first_name} {last_name}',
      'Name',
      `<input name="first_name" value="Ada">
       <input name="last_name" value="Lovelace">`,
    );
    start();
    await flushAsync();

    const heading = document.querySelector('h2');
    expect(heading.children[1].textContent).toBe('Name');
    expect(
      document.querySelector('[data-panel-heading-text]').textContent,
    ).toBe('Ada Lovelace');
  });

  test('setCollapsedLabelText() re-renders on wagtail:panel-toggle', async () => {
    const fieldValues = { first_name: '', last_name: '' };
    setEditHandler(fieldValues);
    setHtml(
      '{first_name} {last_name}',
      'Name',
      `<input name="first_name" value="">
       <input name="last_name" value="">`,
    );
    start();
    await flushAsync();

    const summary = document.querySelector('[data-panel-heading-text]');
    expect(summary.textContent).toBe(' ');

    fieldValues.first_name = 'Grace';
    fieldValues.last_name = 'Hopper';
    document
      .querySelector('[name="first_name"]')
      .dispatchEvent(new Event('input', { bubbles: true }));
    expect(summary.textContent).toBe(' ');

    togglePanel();
    expect(summary.textContent).toBe('Grace Hopper');
  });

  test('connect() does nothing without a heading-text element', async () => {
    setEditHandler({ title: 'Hello' });
    document.body.innerHTML = `
      <section data-controller="w-panel-label" data-w-panel-label-format-value="{title}">
        <input name="title" value="My post">
      </section>
    `;
    start();
    await flushAsync();
    expect(document.querySelector('.w-panel__heading-summary')).toBeNull();
  });

  test('setCollapsedLabelText() gracefully handles a missing editHandler', async () => {
    setHtml('{title}', 'Title', `<input name="title" value="ignored">`);
    start();
    await flushAsync();
    expect(
      document.querySelector('[data-panel-heading-text]').textContent,
    ).toBe('');
  });

  test('setCollapsedLabelText() uses telepath-packed widgets when widgetsId is set', async () => {
    const originalTelepath = window.telepath;
    window.telepath = {
      unpack: () => ({
        first_name: {
          getByName(name, container) {
            return {
              getTextLabel() {
                return container.querySelector(`[name="${name}"]`)?.value || '';
              },
            };
          },
        },
        last_name: {
          getByName(name, container) {
            return {
              getTextLabel() {
                const value =
                  container.querySelector(`[name="${name}"]`)?.value || '';
                return value ? value.toUpperCase() : '';
              },
            };
          },
        },
      }),
    };

    const scriptId = 'id_authors-LABEL_FORMAT_WIDGETS';
    document.body.innerHTML = `
      <script type="application/json" id="${scriptId}">{}</script>
      <section data-controller="w-panel-label"
               data-w-panel-label-format-value="{first_name} {last_name}"
               data-w-panel-label-widgets-id-value="${scriptId}"
               data-w-panel-label-field-prefix-value="authors-0">
        <h2><button data-panel-toggle></button><span data-panel-heading-text>Author</span></h2>
        <input name="authors-0-first_name" value="Ada">
        <input name="authors-0-last_name" value="Lovelace">
      </section>
    `;

    start();
    await flushAsync();
    togglePanel();

    expect(
      document.querySelector('[data-panel-heading-text]').textContent,
    ).toBe('Ada LOVELACE');

    window.telepath = originalTelepath;
  });
});
