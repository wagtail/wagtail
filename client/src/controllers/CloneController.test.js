import { Application } from '@hotwired/stimulus';
import { CloneController } from './CloneController';

jest.useFakeTimers();

describe('CloneController', () => {
  let application;

  afterEach(() => {
    jest.clearAllTimers();
  });

  describe('default behaviour', () => {
    const addedListener = jest.fn();

    document.addEventListener('w-clone:added', addedListener);

    beforeAll(() => {
      application?.stop();
      document.body.innerHTML = `
    <div
      class="messages"
      data-controller="w-clone"
      data-action="w-clone:add@document->w-clone#add"
    >
      <ul data-w-clone-target="container"></ul>
      <template data-w-clone-target="template">
        <li class="success"><span></span></li>
      </template>
    </div>`;

      application = Application.start();
      application.register('w-clone', CloneController);
    });

    it('should not add elements when connected by default', () => {
      expect(document.querySelectorAll('li')).toHaveLength(0);
      expect(addedListener).not.toHaveBeenCalled();
    });

    it('should allow for a message to be added via the add method', () => {
      const text = 'first message text';

      document.dispatchEvent(
        new CustomEvent('w-clone:add', { detail: { text } }),
      );

      // the item should be added
      const item = document.querySelector('li');

      expect(item.classList.toString()).toEqual('success');
      expect(item.lastElementChild.textContent).toEqual(text);

      expect(addedListener).toHaveBeenCalledTimes(1);
    });

    it('should allow for a second message to be added', async () => {
      expect(document.querySelectorAll('li')).toHaveLength(1);

      const text = 'second message text';

      document.dispatchEvent(
        new CustomEvent('w-clone:add', { detail: { text } }),
      );

      expect(document.querySelectorAll('li')).toHaveLength(2);

      // the item should be added
      const item = document.querySelector('li:last-child');

      expect(item.classList.toString()).toEqual('success');
      expect(item.lastElementChild.textContent).toEqual(text);

      expect(addedListener).toHaveBeenCalledTimes(2);
    });

    it('should fall back to default (first) status, if invalid type is provided', async () => {
      expect(document.querySelectorAll('li')).toHaveLength(2);
      const text = 'third message text';
      document.dispatchEvent(
        new CustomEvent('w-clone:add', {
          detail: { text, type: 'invalid' },
        }),
      );
      expect(document.querySelectorAll('li')).toHaveLength(3);
      const item = document.querySelector('li:last-child');
      expect(item.classList.toString()).toEqual('success');
      expect(item.lastElementChild.textContent).toEqual(text);
    });
  });

  describe('additional behaviour', () => {
    beforeAll(() => {
      application?.stop();
      document.body.innerHTML = `
    <div
      class="messages"
      data-controller="w-clone"
      data-action="w-clone:add@document->w-clone#add"
      data-w-clone-added-class="new"
      data-w-clone-show-class="appear"
    >
      <ul data-w-clone-target="container"></ul>
      <template data-w-clone-target="template" data-type="success">
        <li class="success"><span></span></li>
      </template>
      <template data-w-clone-target="template" data-type="error">
        <li class="error"><strong></strong></li>
      </template>
      <template data-w-clone-target="template" data-type="warning">
        <li class="warning"><span></span></li>
      </template>
    </div>`;

      application = Application.start();
      application.register('w-clone', CloneController);
    });

    it('should not add any classes when connected by default', () => {
      expect(document.querySelector('.messages').classList.toString()).toEqual(
        'messages',
      );

      expect(document.querySelectorAll('li')).toHaveLength(0);
    });

    it('should allow for a message to be added via the add method', () => {
      const text = 'first message text';

      document.dispatchEvent(
        new CustomEvent('w-clone:add', { detail: { text } }),
      );

      // set the new class on the container
      expect(
        document.querySelector('.messages').classList.contains('new'),
      ).toBe(true);

      // the item should be added
      const item = document.querySelector('li');

      expect(item.classList.toString()).toEqual('success');
      expect(item.lastElementChild.textContent).toEqual(text);

      // it should add a shown class to the message after the timeout
      jest.runAllTimers();

      expect(document.querySelector('.messages').classList.toString()).toEqual(
        'messages new appear',
      );
    });

    it('should allow for a second message to be added with a specific status', async () => {
      expect(document.querySelectorAll('li')).toHaveLength(1);

      const text = 'second message text';

      document.dispatchEvent(
        new CustomEvent('w-clone:add', {
          detail: { text, type: 'warning' },
        }),
      );

      expect(document.querySelectorAll('li')).toHaveLength(2);

      // the item should be added
      const item = document.querySelector('li:last-child');

      expect(item.classList.toString()).toEqual('warning');
      expect(item.lastElementChild.textContent).toEqual(text);
    });

    it('should allow for any last child in the matched template to have content replaced', async () => {
      expect(document.querySelectorAll('li')).toHaveLength(2);

      const text = 'third message text';

      document.dispatchEvent(
        new CustomEvent('w-clone:add', {
          detail: { text, type: 'error' },
        }),
      );

      expect(document.querySelectorAll('li')).toHaveLength(3);

      // the item should be added
      const item = document.querySelector('li:last-child');

      expect(item.classList.toString()).toEqual('error');
      // note: finding the strong element
      expect(item.querySelector('strong').textContent).toEqual(text);
    });

    it('should allow for items to be cleared when adding a new one', () => {
      expect(document.querySelectorAll('li')).toHaveLength(3);

      const text = 'new message text';

      document.dispatchEvent(
        new CustomEvent('w-clone:add', {
          detail: { clear: true, text, type: 'warning' },
        }),
      );

      expect(document.querySelectorAll('li')).toHaveLength(1);

      const item = document.querySelector('li');

      expect(item.classList.toString()).toEqual('warning');

      expect(item.lastElementChild.textContent).toEqual(text);
    });

    it('should not allow HTML to be added unescaped to any content', () => {
      document.dispatchEvent(
        new CustomEvent('w-clone:add', {
          detail: {
            clear: true,
            text: '<script>window.alert("Secure?");</script>',
            type: 'error',
          },
        }),
      );

      const items = document.querySelectorAll('li');
      expect(items).toHaveLength(1);

      // should escape any text that is passed through
      expect(items[0].outerHTML).toEqual(
        '<li class="error"><strong>&lt;script&gt;window.alert("Secure?");&lt;/script&gt;</strong></li>',
      );
    });
  });
});
