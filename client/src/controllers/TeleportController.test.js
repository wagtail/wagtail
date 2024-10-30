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

      const template = document.getElementById('template');
      const content = template.content.cloneNode(true);

      const targetContainer = document.createElement('div');
      targetContainer.setAttribute('id', 'target-container');
      targetContainer.appendChild(content);
      shadowRoot.appendChild(targetContainer);

      application.start();

      await Promise.resolve();

      expect(shadowRoot.querySelector('#target-container').innerHTML).toContain(
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
});
