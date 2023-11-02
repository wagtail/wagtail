import $ from 'jquery';
import * as StimulusModule from '@hotwired/stimulus';

import { Icon, Portal } from '../..';
import { coreControllerDefinitions } from '../../controllers';
import { escapeHtml } from '../../utils/text';
import { initStimulus } from '../../includes/initStimulus';

/** Expose a global to allow for customisations and packages to build with Stimulus. */
window.StimulusModule = StimulusModule;

/**
 * Wagtail global module, useful for debugging and as the exposed
 * interface to access the Stimulus application instance and base
 * React components.
 *
 * @type {Object} wagtail
 * @property {Object} app - Wagtail's Stimulus application instance.
 * @property {Object} components - Exposed components as globals for third-party reuse.
 * @property {Object} components.Icon - Icon React component.
 * @property {Object} components.Portal - Portal React component.
 */
const wagtail = window.wagtail || {};

/** Initialise Wagtail Stimulus application with core controller definitions. */
wagtail.app = initStimulus({ definitions: coreControllerDefinitions });

/** Expose components as globals for third-party reuse. */
wagtail.components = { Icon, Portal };

window.wagtail = wagtail;

window.escapeHtml = escapeHtml;

/**
 * Enables a "dirty form check", prompting the user if they are navigating away
 * from a page with unsaved changes, as well as optionally controlling other
 * behaviour via a callback
 *
 * It takes the following parameters:
 *
 *  - formSelector - A CSS selector to select the form to apply this check to.
 *
 *  - options - An object for passing in options. Possible options are:
 *  - confirmationMessage - The message to display in the prompt.
 *  - alwaysDirty - When set to true the form will always be considered dirty,
 *    prompting the user even when nothing has been changed.
 *  - commentApp - The CommentApp used by the commenting system, if the dirty check
 *    should include comments
 *  - callback - A function to be run when the dirty status of the form, or the comments
 *    system (if using) changes, taking formDirty, commentsDirty as arguments
 */
function enableDirtyFormCheck(formSelector, options) {
  const $form = $(formSelector);
  const confirmationMessage = options.confirmationMessage || ' ';
  const alwaysDirty = options.alwaysDirty || false;
  const commentApp = options.commentApp || null;
  let initialData = null;
  let formSubmitted = false;

  const updateCallback = (formDirty, commentsDirty) => {
    if (!formDirty && !commentsDirty) {
      document.dispatchEvent(new CustomEvent('w-unsaved:clear'));
      return;
    }

    const [type] = [
      formDirty && commentsDirty && 'all',
      commentsDirty && 'comments',
      formDirty && 'edits',
    ].filter(Boolean);

    document.dispatchEvent(
      new CustomEvent('w-unsaved:add', { detail: { type } }),
    );
  };

  $form.on('submit', () => {
    formSubmitted = true;
  });

  let isDirty = alwaysDirty;
  let isCommentsDirty = false;

  let updateIsCommentsDirtyTimeout = -1;
  if (commentApp) {
    isCommentsDirty = commentApp.selectors.selectIsDirty(
      commentApp.store.getState(),
    );
    commentApp.store.subscribe(() => {
      // Update on a timeout to match the timings for responding to page form changes
      clearTimeout(updateIsCommentsDirtyTimeout);
      updateIsCommentsDirtyTimeout = setTimeout(
        () => {
          const newIsCommentsDirty = commentApp.selectors.selectIsDirty(
            commentApp.store.getState(),
          );
          if (newIsCommentsDirty !== isCommentsDirty) {
            isCommentsDirty = newIsCommentsDirty;
            updateCallback(isDirty, isCommentsDirty);
          }
        },
        isCommentsDirty ? 3000 : 300,
      );
    });
  }

  updateCallback(isDirty, isCommentsDirty);

  let updateIsDirtyTimeout = -1;

  const isFormDirty = () => {
    if (alwaysDirty) {
      return true;
    }
    if (!initialData) {
      return false;
    }

    const formData = new FormData($form[0]);
    const keys = Array.from(formData.keys()).filter(
      (key) => !key.startsWith('comments-'),
    );
    if (keys.length !== initialData.size) {
      return true;
    }

    return keys.some((key) => {
      const newValue = formData.getAll(key);
      const oldValue = initialData.get(key);
      if (newValue === oldValue) {
        return false;
      }
      if (Array.isArray(newValue) && Array.isArray(oldValue)) {
        return (
          newValue.length !== oldValue.length ||
          newValue.some((value, index) => value !== oldValue[index])
        );
      }
      return false;
    });
  };

  const updateIsDirty = () => {
    const previousIsDirty = isDirty;
    isDirty = isFormDirty();
    if (previousIsDirty !== isDirty) {
      updateCallback(isDirty, isCommentsDirty);
    }
  };

  // Delay snapshotting the form’s data to avoid race conditions with form widgets that might process the values.
  // User interaction with the form within that delay also won’t trigger the confirmation message.
  if (!alwaysDirty) {
    setTimeout(() => {
      const initialFormData = new FormData($form[0]);
      initialData = new Map();
      Array.from(initialFormData.keys())
        .filter((key) => !key.startsWith('comments-'))
        .forEach((key) => initialData.set(key, initialFormData.getAll(key)));

      const updateDirtyCheck = () => {
        clearTimeout(updateIsDirtyTimeout);
        // If the form is dirty, it is relatively unlikely to become clean again, so
        // run the dirty check on a relatively long timer that we reset on any form update
        // otherwise, use a short timer both for nicer UX and to ensure widgets
        // like Draftail have time to serialize their data
        updateIsDirtyTimeout = setTimeout(updateIsDirty, isDirty ? 3000 : 300);
      };

      $form.on('change keyup', updateDirtyCheck).trigger('change');

      const isValidInputNode = (node) =>
        node.nodeType === node.ELEMENT_NODE &&
        ['INPUT', 'TEXTAREA', 'SELECT'].includes(node.tagName);

      const observer = new MutationObserver((mutationList) => {
        const hasMutationWithValidInputNode = mutationList.some(
          (mutation) =>
            Array.from(mutation.addedNodes).some(isValidInputNode) ||
            Array.from(mutation.removedNodes).some(isValidInputNode),
        );

        if (hasMutationWithValidInputNode) {
          updateDirtyCheck();
        }
      });

      observer.observe($form[0], {
        childList: true,
        attributes: false,
        subtree: true,
      });
    }, 1000 * 10);
  }

  // eslint-disable-next-line consistent-return
  window.addEventListener('beforeunload', (event) => {
    clearTimeout(updateIsDirtyTimeout);
    updateIsDirty();
    const displayConfirmation = !formSubmitted && (isDirty || isCommentsDirty);

    if (displayConfirmation) {
      // eslint-disable-next-line no-param-reassign
      event.returnValue = confirmationMessage;
      return confirmationMessage;
    }
  });
}

window.enableDirtyFormCheck = enableDirtyFormCheck;

$(() => {
  // eslint-disable-next-line func-names
  $('.dropdown').each(function () {
    const $dropdown = $(this);

    $('.dropdown-toggle', $dropdown).on('click', (e) => {
      e.stopPropagation();
      $dropdown.toggleClass('open');

      if ($dropdown.hasClass('open')) {
        // If a dropdown is opened, add an event listener for document clicks to close it
        $(document).on('click.dropdown.cancel', (e2) => {
          const relTarg = e2.relatedTarget || e2.toElement;

          // Only close dropdown if the click target wasn't a child of this dropdown
          if (!$(relTarg).parents().is($dropdown)) {
            $dropdown.removeClass('open');
            $(document).off('click.dropdown.cancel');
          }
        });
      } else {
        $(document).off('click.dropdown.cancel');
      }
    });
  });

  /* Dropzones */
  $('.drop-zone')
    .on('dragover', function onDragOver() {
      $(this).addClass('hovered');
    })
    .on('dragleave dragend drop', function onDragLeave() {
      $(this).removeClass('hovered');
    });
});
