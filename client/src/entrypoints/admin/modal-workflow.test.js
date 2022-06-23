import $ from 'jquery';

window.$ = $;
window.jQuery = $;

import '../../../../wagtail/admin/static_src/wagtailadmin/js/vendor/bootstrap-modal';
import './modal-workflow';

$.get = jest.fn().mockImplementation((url, data, cb) => {
  cb(
    JSON.stringify({ html: `<div id="url">${url}</div>`, data, step: 'start' }),
  );
  return { fail: jest.fn() };
});

describe('modal-workflow', () => {
  beforeEach(() => {
    document.body.innerHTML =
      '<div id="content"><button class="button action-choose" id="trigger">Open</button></div>';
  });

  it('exposes module as global', () => {
    expect(window.ModalWorkflow).toBeDefined();
  });

  it('should generate a modal when called that is removed when closed', () => {
    let modalWorkflow;

    const openModal = () => {
      modalWorkflow = window.ModalWorkflow({ url: 'path/to/endpoint' });
    };

    expect(document.getElementsByClassName('modal')).toHaveLength(0);

    const triggerButton = document.getElementById('trigger');

    triggerButton.addEventListener('click', openModal);
    triggerButton.dispatchEvent(new MouseEvent('click'));

    // check that modal has been created in the DOM
    const modal = document.getElementsByClassName('modal');
    expect(modal).toHaveLength(1);
    expect(modal).toMatchSnapshot();

    // check that modalWorkflow returns self
    expect(modalWorkflow).toBeInstanceOf(Object);
    expect(modalWorkflow).toHaveProperty('close', expect.any(Function));

    // close modal & check it is removed from the DOM
    modalWorkflow.close();
    expect(document.getElementsByClassName('modal')).toHaveLength(0);
  });

  it('should pull focus from the trigger element to the modal and back to the trigger when closed', () => {
    let modalWorkflow;

    const openModal = () => {
      modalWorkflow = window.ModalWorkflow({ url: 'path/to/endpoint' });
    };

    expect(document.getElementsByClassName('modal')).toHaveLength(0);

    const triggerButton = document.getElementById('trigger');

    triggerButton.focus();
    triggerButton.addEventListener('click', openModal);

    expect(document.activeElement).toEqual(triggerButton);
    triggerButton.dispatchEvent(new MouseEvent('click'));

    // check that modal has been created in the DOM & takes focus
    expect(document.getElementsByClassName('modal')).toHaveLength(1);
    expect(document.activeElement.className).toEqual('modal fade in');

    // close modal & check that focus moves back to the trigger
    modalWorkflow.close();
    expect(document.getElementsByClassName('modal')).toHaveLength(0);
    expect(document.activeElement).toEqual(triggerButton);
  });

  it('should disable the trigger element when the modal is opened and re-enable it when closing', () => {
    let modalWorkflow;

    const openModal = () => {
      modalWorkflow = window.ModalWorkflow({ url: 'path/to/endpoint' });
    };

    expect(document.getElementsByClassName('modal')).toHaveLength(0);

    const triggerButton = document.getElementById('trigger');

    triggerButton.focus();
    triggerButton.addEventListener('click', openModal);
    expect(triggerButton.disabled).toBe(false);
    triggerButton.dispatchEvent(new MouseEvent('click'));

    // check that the trigger button is disabled
    expect(triggerButton.disabled).toBe(true);

    // close modal & check that trigger button is re-enabled
    modalWorkflow.close();
    expect(triggerButton.disabled).toBe(false);
  });

  it('should handle onload and URL param options', () => {
    const onload = { start: jest.fn() };
    const urlParams = { page: 23 };

    let modalWorkflow;

    const openModal = () => {
      modalWorkflow = window.ModalWorkflow({
        url: 'path/to/endpoint',
        urlParams,
        onload,
      });
    };

    expect(onload.start).not.toHaveBeenCalled();
    const triggerButton = document.getElementById('trigger');
    triggerButton.addEventListener('click', openModal);

    const event = new MouseEvent('click');
    triggerButton.dispatchEvent(event);

    expect(modalWorkflow).toBeInstanceOf(Object);

    // important: see mock implementation above, returning a response with injected data to validate behaviour
    const response = {
      data: urlParams,
      html: '<div id="url">path/to/endpoint</div>',
      step: 'start',
    };
    expect(onload.start).toHaveBeenCalledWith(modalWorkflow, response);
  });
});
