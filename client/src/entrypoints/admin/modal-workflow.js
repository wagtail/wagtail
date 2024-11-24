import $ from 'jquery';

import { noop } from '../../utils/noop';
import { gettext } from '../../utils/gettext';

/**
 * ModalWorkflow - A framework for modal popups that are loaded via AJAX.
 *
 * @description
 * Allows navigation to other subpages to happen within the modal.
 * Supports returning a response to the calling page, which may happen after several navigation steps.
 *
 * @param {object} opts
 * @param {string} opts.url - A URL to the view that will be loaded into the dialog.
 *   If not provided and `dialogId` is given, the dialog component's `data-url` attribute is used instead.
 * @param {string=} opts.dialogId - The id of the dialog component to use instead of the Bootstrap modal.
 * @param {Object.<string, function>=} opts.responses - A object of callbacks to be called when the modal content calls `modal.respond(callbackName, params)`
 * @param {Object.<string, function>=} opts.onload - A object of callbacks to be called when loading a step of the workflow.
 *   The 'step' field in the response identifies the callback to call, passing it the
 *   modal object and response data as arguments.
 * @param {HTMLElement=} opts.triggerElement - Element that triggered the modal.
 *   It will be disabled while the modal is shown.
 *   If not provided, defaults to `document.activeElement` (which may not work as expected in Safari).
 * @returns {object}
 */
function ModalWorkflow(opts) {
  const self = {};
  const responseCallbacks = opts.responses || {};
  const errorCallback = opts.onError || noop;
  const useDialog = !!opts.dialogId;

  if (useDialog) {
    self.dialog = document.getElementById(opts.dialogId);
    self.url = opts.url || self.dialog.dataset.url;
    self.body = self.dialog.querySelector('[data-w-dialog-target]');

    // Clear the dialog body as it may have been populated previously
    self.body.innerHTML = '';
  } else {
    /* remove any previous modals before continuing (closing doesn't remove them from the dom) */
    $('body > .modal').remove();

    // Disable the trigger element so it cannot be clicked twice while modal is loading, allow triggerElement to be passed in via opts.
    // Important: Safari will not focus on an element on click so activeElement will not be set as expected
    // https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button#clicking_and_focus
    // https://bugs.webkit.org/show_bug.cgi?id=22261
    self.triggerElement = opts.triggerElement || document.activeElement;
    self.triggerElement.setAttribute('disabled', true);

    // set default contents of container
    const iconClose =
      '<svg class="icon icon-cross" aria-hidden="true"><use href="#icon-cross"></use></svg>';
    self.container = $(
      '<div class="modal fade" tabindex="-1" role="dialog" aria-hidden="true">\n  <div class="modal-dialog">\n    <div class="modal-content">\n      <button type="button" class="button close button--icon text-replace" data-dismiss="modal">' +
        iconClose +
        gettext('Close') +
        '</button>\n      <div class="modal-body"></div>\n    </div><!-- /.modal-content -->\n  </div><!-- /.modal-dialog -->\n</div>',
    );

    // add container to body and hide it, so content can be added to it before display
    $('body').append(self.container);
    self.container.modal('hide');

    // add listener - once modal is about to be hidden, re-enable the trigger unless it's been forcibly
    // disabled by adding a `data-force-disabled` attribute; this mechanism is necessary to accommodate
    // response handlers that disable the trigger to prevent it from reopening
    self.container.on('hide.bs.modal', () => {
      if (!self.triggerElement.hasAttribute('data-force-disabled')) {
        self.triggerElement.removeAttribute('disabled');
        // support w-progress controller reset if activated on the button's click
        self.triggerElement.removeAttribute('data-w-progress-loading-value');
      }
    });

    // add listener - once modal is fully hidden (closed & css transitions end) - re-focus on trigger and remove from DOM
    self.container.on('hidden.bs.modal', () => {
      self.triggerElement.focus();
      self.container.remove();
    });

    self.url = opts.url;
    self.body = self.container.find('.modal-body');
  }

  self.loadUrl = function loadUrl(url, urlParams) {
    $.get(url, urlParams, self.loadResponseText, 'text').fail(errorCallback);
  };

  self.postForm = function postForm(url, formData) {
    $.post(url, formData, self.loadResponseText, 'text').fail(errorCallback);
  };

  self.ajaxifyForm = function ajaxifyForm(formSelector) {
    $(formSelector).each(function ajaxifyFormInner() {
      const action = this.action;
      if (this.method.toLowerCase() === 'get') {
        $(this).on('submit', function handleSubmit() {
          self.loadUrl(action, $(this).serialize());
          return false;
        });
      } else {
        $(this).on('submit', function handleSubmit() {
          self.postForm(action, $(this).serialize());
          return false;
        });
      }
    });
  };

  self.loadResponseText = function loadResponseText(responseText) {
    const response = JSON.parse(responseText);
    self.loadBody(response);
  };

  self.loadBody = function loadBody(response) {
    if (response.html) {
      // if response contains an 'html' item, replace modal body with it
      if (useDialog) {
        self.body.innerHTML = response.html;
      } else {
        self.body.html(response.html);
        self.container.modal('show');
      }
    }

    /* If response contains a 'step' identifier, and that identifier is found in
    the onload dict, call that onload handler */
    if (opts.onload && response.step && response.step in opts.onload) {
      opts.onload[response.step](self, response);
    }
  };

  self.respond = function handleResponse(responseType) {
    if (responseType in responseCallbacks) {
      const args = Array.prototype.slice.call(arguments, 1); // eslint-disable-line prefer-rest-params
      responseCallbacks[responseType].apply(self, args);
    }
  };

  self.close = function handleClose() {
    if (useDialog) {
      self.dialog.dispatchEvent(new CustomEvent('w-dialog:hide'));
    } else {
      self.container.modal('hide');
    }
  };

  self.loadUrl(self.url, opts.urlParams);

  return self;
}

window.ModalWorkflow = ModalWorkflow;
