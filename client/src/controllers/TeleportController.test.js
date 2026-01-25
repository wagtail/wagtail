import { Application } from '@hotwired/stimulus';

import { TeleportController } from './TeleportController';

describe('TeleportController', () => {
  let application;

  describe('basic behavior', () => {
    beforeEach(() => {
      application?.stop();

      document.body.innerHTML = `
        <main>
          <template id="template" data-controller="w-teleport">
            <div id="content">Some content</div>
          </template>
        </main>`;

      application = new Application();
      application.register('w-teleport', TeleportController);
    });

    it('should move the Template element content to the body and remove the template by default', async () => {
      expect(document.querySelectorAll('template')).toHaveLength(1);
      expect(document.getElementById('content')).toBeNull();

      const appendCallback = jest.fn();
      document.addEventListener('w-teleport:append', appendCallback);
      const appendedCallback = jest.fn();
      document.addEventListener('w-teleport:appended', appendedCallback);

      application.start();

      await Promise.resolve();

      // updating the DOM

      expect(document.querySelectorAll('template')).toHaveLength(0);
      expect(document.getElementById('content')).not.toBeNull();
      expect(document.getElementById('content').parentElement).toEqual(
        document.body,
      );

      // dispatching events

      expect(appendCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: { complete: expect.any(Function), target: document.body },
        }),
      );
      expect(appendedCallback).toHaveBeenCalledWith(
        expect.objectContaining({ detail: { target: document.body } }),
      );
    });

    it('should allow a value to have the Template element kept', async () => {
      document
        .querySelector('template')
        .setAttribute('data-w-teleport-keep-value', 'true');

      expect(document.querySelectorAll('template')).toHaveLength(1);
      expect(document.getElementById('content')).toBeNull();

      application.start();

      await Promise.resolve();

      expect(document.querySelectorAll('template')).toHaveLength(1);
      expect(document.getElementById('content')).not.toBeNull();
      expect(document.getElementById('content').parentElement).toEqual(
        document.body,
      );
    });

    it('should allow the target container to be based on a provided selector value', async () => {
      document.body.innerHTML += `
        <div id="target-container"></div>
        `;

      const template = document.querySelector('template');
      template.setAttribute(
        'data-w-teleport-target-value',
        '#target-container',
      );

      expect(document.getElementById('target-container').innerHTML).toEqual('');

      application.start();

      await Promise.resolve();

      expect(
        document.getElementById('target-container').innerHTML.trim(),
      ).toEqual('<div id="content">Some content</div>');
    });

    it('should allow for a default target container within the root element of a shadow DOM', async () => {
      const shadowHost = document.createElement('div');
      const shadowRoot = shadowHost.attachShadow({ mode: 'open' });
      document.body.appendChild(shadowHost);

      shadowRoot.innerHTML = /* html */ `
        <div>
          <aside>
            <!--
            The template will be moved here, and then the content will be
            teleported to the <div> (first child of the shadow root)
            when the app starts
            -->
          </aside>
        </div>
      `;

      // Move the template to the aside element
      const aside = shadowRoot.querySelector('aside');
      const template = document.getElementById('template');
      aside.append(template);

      // Create a new application with the shadow DOM as the root element
      application = new Application(shadowRoot.firstElementChild);
      application.register('w-teleport', TeleportController);
      application.start();

      await Promise.resolve();

      application.stop();

      // Without an explicit target, the content should be teleported to the
      // first child of the shadow root
      expect(shadowRoot.firstElementChild.innerHTML).toContain(
        '<div id="content">Some content</div>',
      );
      // The template should be removed from the DOM
      expect(shadowRoot.querySelector('template')).toBeNull();
    });

    it('should allow for a custom target container within the shadow root', async () => {
      const shadowHost = document.createElement('div');
      const shadowRoot = shadowHost.attachShadow({ mode: 'open' });
      document.body.append(shadowHost);

      // Create a custom target container within the shadow DOM
      shadowRoot.innerHTML = /* html */ `
        <div>
          <aside data-my-element="foo"></aside>
          <!--
           The template will be moved here, and then the content will be
           teleported to the <aside> when the app starts
          -->
        </div>
      `;

      // Move the template to the shadow DOM
      const template = document.getElementById('template');
      shadowRoot.firstElementChild.append(template);
      template.setAttribute(
        'data-w-teleport-target-value',
        '[data-my-element]',
      );

      // Create a new application with the shadow DOM as the root element
      application = new Application(shadowRoot.firstElementChild);
      application.register('w-teleport', TeleportController);
      application.start();

      await Promise.resolve();

      application.stop();

      // The content should be teleported to the <aside> element
      expect(shadowRoot.querySelector('[data-my-element]').innerHTML).toContain(
        '<div id="content">Some content</div>',
      );
      // The template should be removed from the DOM
      expect(shadowRoot.querySelector('template')).toBeNull();
    });

    it('should look in the document if the target is not found in the shadow DOM', async () => {
      // Create a custom target container in the document body
      const fallbackTarget = document.createElement('aside');
      fallbackTarget.setAttribute('data-my-element', 'bar');
      document.body.append(fallbackTarget);

      const shadowHost = document.createElement('div');
      const shadowRoot = shadowHost.attachShadow({ mode: 'open' });
      document.body.append(shadowHost);

      // Create an element in the shadow DOM that will not match the target
      shadowRoot.innerHTML = /* html */ `
        <div>
          <aside data-my-element="foo"></aside>
          <!--
           The template will be moved here, and then the content will be
           teleported to the <aside data-my-element="bar"> outside of the shadow
           DOM when the app starts
          -->
        </div>
      `;

      // Move the template to the shadow DOM
      const template = document.getElementById('template');
      shadowRoot.firstElementChild.append(template);
      template.setAttribute(
        'data-w-teleport-target-value',
        '[data-my-element="bar"]',
      );

      // Create a new application with the shadow DOM as the root element
      application = new Application(shadowRoot.firstElementChild);
      application.register('w-teleport', TeleportController);
      application.start();

      await Promise.resolve();

      application.stop();

      // The content should not be teleported to the <aside> element in the shadow DOM
      expect(shadowRoot.querySelector('[data-my-element]').innerHTML).toEqual(
        '',
      );
      // The template should be removed from the DOM and does not exist in the body
      expect(shadowRoot.querySelector('template')).toBeNull();
      expect(document.querySelector('template')).toBeNull();
      // The content should be teleported to the <aside> element in the document body
      expect(fallbackTarget.innerHTML).toContain(
        '<div id="content">Some content</div>',
      );
    });

    it('should clear the target container if the reset value is set to true', async () => {
      document.body.innerHTML += `
        <div id="target-container"><p>I should not be here</p></div>
        `;

      const template = document.querySelector('template');
      template.setAttribute(
        'data-w-teleport-target-value',
        '#target-container',
      );
      template.setAttribute('data-w-teleport-reset-value', 'true');

      expect(document.getElementById('target-container').innerHTML).toEqual(
        '<p>I should not be here</p>',
      );

      application.start();

      await Promise.resolve();

      expect(
        document.getElementById('target-container').innerHTML.trim(),
      ).toEqual('<div id="content">Some content</div>');
    });

    it('should not clear the target container if the reset value is unset (false)', async () => {
      document.body.innerHTML += `
        <div id="target-container"><p>I should still be here</p></div>
        `;

      const template = document.querySelector('template');
      template.setAttribute(
        'data-w-teleport-target-value',
        '#target-container',
      );

      expect(document.getElementById('target-container').innerHTML).toEqual(
        '<p>I should still be here</p>',
      );

      application.start();

      await Promise.resolve();

      const contents = document.getElementById('target-container').innerHTML;
      expect(contents).toContain('<p>I should still be here</p>');
      expect(contents).toContain('<div id="content">Some content</div>');
    });

    it('should allow the template to contain multiple children', async () => {
      document.body.innerHTML += `
        <div id="target-container"></div>
        `;

      const template = document.querySelector('template');
      template.setAttribute(
        'data-w-teleport-target-value',
        '#target-container',
      );

      const otherTemplateContent = document.createElement('div');
      otherTemplateContent.innerHTML = 'Other content';
      otherTemplateContent.id = 'other-content';
      template.content.appendChild(otherTemplateContent);

      expect(document.getElementById('target-container').innerHTML).toEqual('');

      application.start();

      await Promise.resolve();

      const container = document.getElementById('target-container');
      const content = container.querySelector('#content');
      const otherContent = container.querySelector('#other-content');
      expect(content).not.toBeNull();
      expect(otherContent).not.toBeNull();
      expect(content.innerHTML.trim()).toEqual('Some content');
      expect(otherContent.innerHTML.trim()).toEqual('Other content');
    });

    it('should not throw an error if the template content is empty', async () => {
      document.body.innerHTML += `
        <div id="target-container"><p>I should still be here</p></div>
        `;

      const template = document.querySelector('template');
      template.setAttribute(
        'data-w-teleport-target-value',
        '#target-container',
      );

      expect(document.getElementById('target-container').innerHTML).toEqual(
        '<p>I should still be here</p>',
      );

      const errors = [];

      document.getElementById('template').innerHTML = '';
      application.handleError = (error, message) => {
        errors.push({ error, message });
      };

      await Promise.resolve(application.start());

      expect(errors).toEqual([]);

      expect(document.getElementById('target-container').innerHTML).toEqual(
        '<p>I should still be here</p>',
      );
    });

    it('should allow erasing the target container by using an empty template with reset value set to true', async () => {
      document.body.innerHTML += `
        <div id="target-container"><p>I should not be here</p></div>
        `;

      const template = document.querySelector('template');
      template.setAttribute(
        'data-w-teleport-target-value',
        '#target-container',
      );
      template.setAttribute('data-w-teleport-reset-value', 'true');
      const errors = [];

      document.getElementById('template').innerHTML = '';

      application.handleError = (error, message) => {
        errors.push({ error, message });
      };

      await Promise.resolve(application.start());

      expect(errors).toEqual([]);

      const contents = document.getElementById('target-container').innerHTML;
      expect(contents).toEqual('');
    });

    it('should run inline scripts contained in the template content', async () => {
      document.body.innerHTML += /* html */ `
        <div id="target-container"></div>
      `;

      const template = document.querySelector('template');
      template.setAttribute(
        'data-w-teleport-target-value',
        '#target-container',
      );

      const scriptContent = /* js */ `
        document.getElementById('target-container').setAttribute('data-script-ran', 'true');
      `;
      const scriptElement = document.createElement('script');
      scriptElement.text = scriptContent;
      template.content.appendChild(scriptElement);

      expect(document.getElementById('target-container').innerHTML).toEqual('');

      application.start();

      await Promise.resolve();

      const container = document.getElementById('target-container');
      expect(container).not.toBeNull();
      expect(container.getAttribute('data-script-ran')).toEqual('true');
    });

    it('should throw an error if a valid target container cannot be resolved', async () => {
      const errors = [];

      document
        .getElementById('template')
        .setAttribute('data-w-teleport-target-value', '#missing-container');

      application.handleError = (error, message) => {
        errors.push({ error, message });
      };

      await Promise.resolve(application.start());

      expect(errors).toEqual([
        {
          error: new Error(
            "No valid target container found at '#missing-container'.",
          ),
          message: 'Error connecting controller',
        },
      ]);
    });
  });

  describe('mode value', () => {
    const startController = async () => {
      application.start();
      await Promise.resolve();
    };

    const setTemplateMode = (mode) => {
      const template = document.getElementById('template');
      template.setAttribute('data-w-teleport-mode-value', mode);

      return template;
    };

    beforeEach(() => {
      application?.stop();
      document.body.innerHTML = /* html */ `
        <main>
          <template
            id="template"
            data-controller="w-teleport"
            data-w-teleport-target-value="#target"
          >
            <p id="teleported-element">Element node</p>
            and + some text node
            <script>document.body.setAttribute('data-script-ran', 'true');</script>
          </template>
          <section id="target-parent">
            <div id="target">
              Some existing text
              <span id="existing-child">Existing child element</span>
            </div>
          </section>
        </main>
      `;

      application = new Application();
      application.register('w-teleport', TeleportController);
    });

    afterEach(() => {
      application?.stop();
    });

    it('replaces the target element when mode is outerHTML', async () => {
      setTemplateMode('outerHTML');
      await startController();
      expect(document.body.outerHTML).toMatchSnapshot();
    });

    it('replaces the target inner content when mode is innerHTML', async () => {
      setTemplateMode('innerHTML');
      await startController();
      expect(document.body.outerHTML).toMatchSnapshot();
    });

    it('copies only the textual content when mode is textContent', async () => {
      setTemplateMode('textContent');
      await startController();
      expect(document.body.outerHTML).toMatchSnapshot();
    });

    it('inserts nodes before the target when mode is beforebegin', async () => {
      setTemplateMode('beforebegin');
      await startController();
      expect(document.body.outerHTML).toMatchSnapshot();
    });

    it('prepends nodes when mode is afterbegin', async () => {
      setTemplateMode('afterbegin');
      await startController();
      expect(document.body.outerHTML).toMatchSnapshot();
    });

    it('appends nodes when mode is beforeend', async () => {
      setTemplateMode('beforeend');
      await startController();
      expect(document.body.outerHTML).toMatchSnapshot();
    });

    it('inserts nodes after the target when mode is afterend', async () => {
      setTemplateMode('afterend');
      await startController();
      expect(document.body.outerHTML).toMatchSnapshot();
    });

    it('defaults to beforeend if mode is not recognised', async () => {
      setTemplateMode('unknown');
      await startController();
      expect(document.body.outerHTML).toMatchSnapshot();
    });
  });
});
