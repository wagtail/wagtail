import { Application } from '@hotwired/stimulus';
import { CloneController } from './CloneController';

jest.useFakeTimers();
jest.spyOn(global, 'setTimeout');

describe('CloneController', () => {
  let application;

  afterEach(() => {
    jest.clearAllTimers();
  });

  describe('default behavior', () => {
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

  describe('additional behavior', () => {
    beforeAll(() => {
      application?.stop();
      document.body.innerHTML = `
    <div
      class="messages w-hidden"
      data-controller="w-clone"
      data-action="w-clone:add@document->w-clone#add w-clone:clear@document->w-clone#clear"
      data-w-clone-added-class="new"
      data-w-clone-hide-class="w-hidden"
      data-w-clone-show-class="appear"
      data-w-clone-show-delay-value="500"
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
        'messages w-hidden',
      );

      expect(document.querySelectorAll('li')).toHaveLength(0);
    });

    it('should allow for a message to be added via the add method', async () => {
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
      await jest.runAllTimersAsync();

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

    it('should allow the clear method to be called with an action, also updating classes', async () => {
      const startingClasses = 'messages w-hidden';
      const element = document.querySelector('.messages');
      const clearEventHandler = jest.fn();
      element.addEventListener('w-clone:cleared', clearEventHandler, {
        once: true,
      });

      // change delay to be zero (updates immediately)
      element.setAttribute('data-w-clone-show-delay-value', '0');
      // reset classes
      element.className = startingClasses;
      expect(element.classList.toString()).toEqual('messages w-hidden');

      document.dispatchEvent(new CustomEvent('w-clone:add'));
      document.dispatchEvent(new CustomEvent('w-clone:add'));

      expect(document.querySelectorAll('li')).toHaveLength(3);
      expect(element.classList.toString()).toEqual('messages new appear');

      document.dispatchEvent(new CustomEvent('w-clone:clear'));

      await jest.runAllTimersAsync();

      expect(document.querySelectorAll('li')).toHaveLength(0);
      expect(element.classList.toString()).toEqual(startingClasses);
      expect(clearEventHandler).toHaveBeenCalledTimes(1);
    });

    it('should allow the clear method to be called with a delay', async () => {
      const startingClasses = 'messages w-hidden';
      const element = document.querySelector('.messages');
      const clearEventHandler = jest.fn();
      element.addEventListener('w-clone:cleared', clearEventHandler, {
        once: true,
      });

      // set up clear delay
      element.setAttribute('data-w-clone-clear-delay-value', '1024');
      // change delay to be zero (updates immediately)
      element.setAttribute('data-w-clone-show-delay-value', '0');
      // reset classes
      element.className = startingClasses;
      expect(element.classList.toString()).toEqual('messages w-hidden');

      document.dispatchEvent(new CustomEvent('w-clone:add'));
      document.dispatchEvent(new CustomEvent('w-clone:add'));

      expect(document.querySelectorAll('li')).toHaveLength(2);
      expect(element.classList.toString()).toEqual('messages new appear');

      document.dispatchEvent(new CustomEvent('w-clone:clear'));

      expect(setTimeout).toHaveBeenLastCalledWith(expect.any(Function), 1024);

      expect(document.querySelectorAll('li')).toHaveLength(2);

      await Promise.resolve(jest.advanceTimersByTime(1000));

      document.dispatchEvent(new CustomEvent('w-clone:clear')); // ensure duplicate calls work correctly

      expect(document.querySelectorAll('li')).toHaveLength(2);

      await Promise.resolve(jest.advanceTimersByTime(25));

      expect(document.querySelectorAll('li')).toHaveLength(0);
      expect(element.classList.toString()).toEqual(startingClasses);
      expect(clearEventHandler).toHaveBeenCalledTimes(1);
    });
  });

  describe('auto clearing after a determined delay', () => {
    beforeAll(() => {
      application?.stop();
      document.body.innerHTML = `
    <div
      class="messages"
      data-controller="w-clone"
      data-action="w-clone:add@document->w-clone#add"
      data-w-clone-auto-clear-value="500"
    >
      <div data-w-clone-target="container"></div>
      <template data-w-clone-target="template">
        <span class="message">Message</span>
      </template>
    </div>`;

      application = Application.start();
      application.register('w-clone', CloneController);
    });

    it('should allow for a message to be added via the add method & have it clear automatically', async () => {
      expect(document.querySelectorAll('.message')).toHaveLength(0);

      document.dispatchEvent(new CustomEvent('w-clone:add'));

      await Promise.resolve();

      expect(document.querySelectorAll('.message')).toHaveLength(1);

      await Promise.resolve(jest.advanceTimersByTime(550));

      expect(document.querySelectorAll('.message')).toHaveLength(0);
    });
  });
});
