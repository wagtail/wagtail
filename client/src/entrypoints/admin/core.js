import $ from 'jquery';

import { coreControllerDefinitions } from '../../controllers';
import { escapeHtml } from '../../utils/text';
import { initStimulus } from '../../includes/initStimulus';
import { initTagField } from '../../includes/initTagField';
import { initTooltips } from '../../includes/initTooltips';

/** initialise Wagtail Stimulus application with core controller definitions */
window.Stimulus = initStimulus({ definitions: coreControllerDefinitions });

window.escapeHtml = escapeHtml;

window.initTagField = initTagField;

/*
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
  const callback = options.callback || null;
  let initialData = null;
  let formSubmitted = false;

  const updateCallback = (formDirty, commentsDirty) => {
    if (callback) {
      callback(formDirty, commentsDirty);
    }
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
  // Add class to the body from which transitions may be hung so they don't appear to transition as the page loads
  $('body').addClass('ready');

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

  /* Header search behaviour */
  if (window.headerSearch) {
    let searchCurrentIndex = 0;
    let searchNextIndex = 0;
    const $input = $(window.headerSearch.termInput);
    const $inputContainer = $input.parent();
    const $icon = $inputContainer.find('use');
    const baseIcon = $icon.attr('href');

    $input.on('keyup cut paste change', () => {
      clearTimeout($input.data('timer'));
      // eslint-disable-next-line @typescript-eslint/no-use-before-define
      $input.data('timer', setTimeout(search, 200));
    });

    // auto focus on search box
    $input.trigger('focus');

    // eslint-disable-next-line func-names
    const search = function () {
      const newQuery = $input.val();
      const searchParams = new URLSearchParams(window.location.search);
      const currentQuery = searchParams.get('q') || '';
      // only do the query if it has changed for trimmed queries
      // for example - " " === "" and "firstword " ==== "firstword"
      if (currentQuery.trim() !== newQuery.trim()) {
        $icon.attr('href', '#icon-spinner');
        searchNextIndex += 1;
        const index = searchNextIndex;

        // Update q, reset to first page, and keep other query params
        searchParams.set('q', newQuery);
        searchParams.delete('p');
        const queryString = searchParams.toString();

        $.ajax({
          url: window.headerSearch.url,
          data: queryString,
          success(data) {
            if (index > searchCurrentIndex) {
              searchCurrentIndex = index;
              $(window.headerSearch.targetOutput).html(data).slideDown(800);
              window.history.replaceState(null, null, '?' + queryString);
              $input[0].dispatchEvent(new Event('search-success'));
            }
          },
          complete() {
            window.wagtail.ui.initDropDowns();
            // Reinitialise any tooltips
            initTooltips();
            $icon.attr('href', baseIcon);
          },
        });
      }
    };
  }
});

// =============================================================================
// Wagtail global module, mainly useful for debugging.
// =============================================================================

// =============================================================================
// Inline dropdown module
// =============================================================================

const wagtail = window.wagtail || {};
if (!wagtail.ui) {
  wagtail.ui = {};
}

// Constants
const DROPDOWN_SELECTOR = '[data-dropdown]';
const LISTING_TITLE_SELECTOR = '[data-listing-page-title]';
const LISTING_ACTIVE_CLASS = 'listing__item--active';
const IS_OPEN = 'is-open';
const clickEvent = 'click';
const ARIA = 'aria-hidden';
const keys = {
  ESC: 27,
  ENTER: 13,
  SPACE: 32,
};

/**
 * Singleton controller and registry for DropDown components.
 *
 * Mostly used to maintain open/closed state of components and easily
 * toggle them when the focus changes.
 */
const DropDownController = {
  dropDowns: [],

  closeAllExcept(dropDown) {
    const index = this.dropDowns.indexOf(dropDown);

    this.dropDowns.forEach((item, i) => {
      if (i !== index && item.state.isOpen) {
        item.closeDropDown();
      }
    });
  },

  add(dropDown) {
    this.dropDowns.push(dropDown);
  },

  get() {
    return this.dropDowns;
  },

  getByIndex(index) {
    return this.dropDowns[index];
  },

  getOpenDropDown() {
    let needle = null;

    this.dropDowns.forEach((item) => {
      if (item.state.isOpen) {
        needle = item;
      }
    });

    return needle;
  },
};

/**
 * DropDown component
 *
 * Template: _button_with_dropdown.html
 *
 * Can contain a list of links
 * Controllable via a toggle class or the keyboard.
 */
function DropDown(el, registry) {
  if (!el || !registry) {
    if ('error' in console) {
      // eslint-disable-next-line no-console
      console.error(
        'A dropdown was created without an element or the DropDownController.\nMake sure to pass both to your component.',
      );
      return;
    }
  }

  this.el = el;
  this.$parent = $(el).parents(LISTING_TITLE_SELECTOR);

  this.state = {
    isOpen: false,
  };

  this.registry = registry;

  this.clickOutsideDropDown = this.clickOutsideDropDown.bind(this);
  this.closeDropDown = this.closeDropDown.bind(this);
  this.openDropDown = this.openDropDown.bind(this);
  this.handleClick = this.handleClick.bind(this);
  this.handleKeyEvent = this.handleKeyEvent.bind(this);

  el.addEventListener(clickEvent, this.handleClick);
  el.addEventListener('keydown', this.handleKeyEvent);
  this.$parent.data('close', this.closeDropDown);
}

DropDown.prototype = {
  handleKeyEvent(e) {
    const validTriggers = [keys.SPACE, keys.ENTER];

    if (validTriggers.indexOf(e.which) > -1) {
      e.preventDefault();
      this.handleClick(e);
    }
  },

  handleClick(e) {
    if (!this.state.isOpen) {
      this.openDropDown(e);
    } else {
      this.closeDropDown(e);
    }
  },

  openDropDown(e) {
    e.stopPropagation();
    e.preventDefault();
    const el = this.el;
    const $parent = this.$parent;

    this.state.isOpen = true;
    this.registry.closeAllExcept(this);

    el.classList.add(IS_OPEN);
    el.setAttribute(ARIA, false);
    document.addEventListener(clickEvent, this.clickOutsideDropDown, false);
    $parent.addClass(LISTING_ACTIVE_CLASS);
  },

  closeDropDown() {
    this.state.isOpen = false;

    const el = this.el;
    const $parent = this.$parent;
    document.removeEventListener(clickEvent, this.clickOutsideDropDown, false);
    el.classList.remove(IS_OPEN);
    el.setAttribute(ARIA, true);
    $parent.removeClass(LISTING_ACTIVE_CLASS);
  },

  clickOutsideDropDown(e) {
    const el = this.el;
    const relTarget = e.relatedTarget || e.toElement;

    if (!$(relTarget).parents().is(el)) {
      this.closeDropDown();
    }
  },
};

function initDropDown() {
  const dropDown = new DropDown(this, DropDownController);
  DropDownController.add(dropDown);
}

function handleKeyPress(e) {
  if (e.which === keys.ESC) {
    const open = DropDownController.getOpenDropDown();
    if (open) {
      open.closeDropDown();
    }
  }
}

function initDropDowns() {
  $(DROPDOWN_SELECTOR).each(initDropDown);
  $(document).on('keydown', handleKeyPress);
}

$(document).ready(initDropDowns);
wagtail.ui.initDropDowns = initDropDowns;
wagtail.ui.DropDownController = DropDownController;

window.wagtail = wagtail;
