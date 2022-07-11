import $ from 'jquery';
import { cleanForSlug } from '../../utils/text';

function InlinePanel(opts) {
  // lgtm[js/unused-local-variable]
  const self = {};

  // eslint-disable-next-line func-names
  self.setHasContent = function () {
    if ($('> li', self.formsUl).not('.deleted').length) {
      self.formsUl.parent().removeClass('empty');
    } else {
      self.formsUl.parent().addClass('empty');
    }
  };

  // eslint-disable-next-line func-names
  self.initChildControls = function (prefix) {
    const childId = 'inline_child_' + prefix;
    const deleteInputId = 'id_' + prefix + '-DELETE';

    // mark container as having children to identify fields in use from those not
    self.setHasContent();

    $('#' + deleteInputId + '-button').on('click', () => {
      /* set 'deleted' form field to true */
      $('#' + deleteInputId).val('1');
      $('#' + childId)
        .addClass('deleted')
        .slideUp(() => {
          self.updateMoveButtonDisabledStates();
          self.updateAddButtonState();
          self.setHasContent();
        });
    });

    if (opts.canOrder) {
      $('#' + prefix + '-move-up').on('click', () => {
        const currentChild = $('#' + childId);
        const currentChildOrderElem = currentChild.children(
          'input[name$="-ORDER"]',
        );
        const currentChildOrder = currentChildOrderElem.val();

        /* find the previous visible 'inline_child' li before this one */
        const prevChild = currentChild.prevAll(':not(.deleted)').first();
        if (!prevChild.length) return;
        const prevChildOrderElem = prevChild.children('input[name$="-ORDER"]');
        const prevChildOrder = prevChildOrderElem.val();

        // async swap animation must run before the insertBefore line below, but doesn't need to finish first
        self.animateSwap(currentChild, prevChild);

        currentChild.insertBefore(prevChild);
        currentChildOrderElem.val(prevChildOrder);
        prevChildOrderElem.val(currentChildOrder);

        self.updateMoveButtonDisabledStates();
      });

      $('#' + prefix + '-move-down').on('click', () => {
        const currentChild = $('#' + childId);
        const currentChildOrderElem = currentChild.children(
          'input[name$="-ORDER"]',
        );
        const currentChildOrder = currentChildOrderElem.val();

        /* find the next visible 'inline_child' li after this one */
        const nextChild = currentChild.nextAll(':not(.deleted)').first();
        if (!nextChild.length) return;
        const nextChildOrderElem = nextChild.children('input[name$="-ORDER"]');
        const nextChildOrder = nextChildOrderElem.val();

        // async swap animation must run before the insertAfter line below, but doesn't need to finish first
        self.animateSwap(currentChild, nextChild);

        currentChild.insertAfter(nextChild);
        currentChildOrderElem.val(nextChildOrder);
        nextChildOrderElem.val(currentChildOrder);

        self.updateMoveButtonDisabledStates();
      });
    }

    /* Hide container on page load if it is marked as deleted. Remove the error
     message so that it doesn't count towards the number of errors on the tab at the
     top of the page. */
    if ($('#' + deleteInputId).val() === '1') {
      $('#' + childId)
        .addClass('deleted')
        .hide(0, () => {
          self.updateMoveButtonDisabledStates();
          self.updateAddButtonState();
          self.setHasContent();
        });

      $('#' + childId)
        .find('.error-message')
        .remove();
    }
  };

  self.formsUl = $('#' + opts.formsetPrefix + '-FORMS');

  // eslint-disable-next-line func-names
  self.updateMoveButtonDisabledStates = function () {
    if (opts.canOrder) {
      const forms = self.formsUl.children('li:not(.deleted)');
      // eslint-disable-next-line func-names
      forms.each(function (i) {
        $('ul.controls .inline-child-move-up', this)
          .toggleClass('disabled', i === 0)
          .toggleClass('enabled', i !== 0);
        $('ul.controls .inline-child-move-down', this)
          .toggleClass('disabled', i === forms.length - 1)
          .toggleClass('enabled', i !== forms.length - 1);
      });
    }
  };

  // eslint-disable-next-line func-names
  self.updateAddButtonState = function () {
    if (opts.maxForms) {
      const forms = $('> [data-inline-panel-child]', self.formsUl).not(
        '.deleted',
      );
      const addButton = $('#' + opts.formsetPrefix + '-ADD');

      if (forms.length >= opts.maxForms) {
        addButton.addClass('disabled');
      } else {
        addButton.removeClass('disabled');
      }
    }
  };

  // eslint-disable-next-line func-names
  self.animateSwap = function (item1, item2) {
    const parent = self.formsUl;
    const children = parent.children('li:not(.deleted)');

    // Apply moving class to container (ul.multiple) so it can assist absolute positioning of it's children
    // Also set it's relatively calculated height to be an absolute one,
    // to prevent the containercollapsing while its children go absolute
    parent.addClass('moving').css('height', parent.height());

    children
      .each(function moveChildTop() {
        $(this).css('top', $(this).position().top);
      })
      .addClass('moving');

    // animate swapping around
    item1.animate(
      {
        top: item2.position().top,
      },
      200,
      () => {
        parent.removeClass('moving').removeAttr('style');
        children.removeClass('moving').removeAttr('style');
      },
    );

    item2.animate(
      {
        top: item1.position().top,
      },
      200,
      () => {
        parent.removeClass('moving').removeAttr('style');
        children.removeClass('moving').removeAttr('style');
      },
    );
  };

  // eslint-disable-next-line no-undef
  buildExpandingFormset(opts.formsetPrefix, {
    onAdd(formCount) {
      const newChildPrefix = opts.emptyChildFormPrefix.replace(
        /__prefix__/g,
        formCount,
      );
      self.initChildControls(newChildPrefix);
      if (opts.canOrder) {
        /* NB form hidden inputs use 0-based index and only increment formCount *after* this function is run.
        Therefore formcount and order are currently equal and order must be incremented
        to ensure it's *greater* than previous item */
        $('#id_' + newChildPrefix + '-ORDER').val(formCount + 1);
      }

      self.updateMoveButtonDisabledStates();
      self.updateAddButtonState();

      if (opts.onAdd) opts.onAdd();
    },
  });

  return self;
}

window.InlinePanel = InlinePanel;

window.cleanForSlug = cleanForSlug;

function initSlugAutoPopulate() {
  let slugFollowsTitle = false;

  // eslint-disable-next-line func-names
  $('#id_title').on('focus', function () {
    /* slug should only follow the title field if its value matched the title's value at the time of focus */
    const currentSlug = $('#id_slug').val();
    const slugifiedTitle = cleanForSlug(this.value, true);
    slugFollowsTitle = currentSlug === slugifiedTitle;
  });

  // eslint-disable-next-line func-names
  $('#id_title').on('keyup keydown keypress blur', function () {
    if (slugFollowsTitle) {
      const slugifiedTitle = cleanForSlug(this.value, true);
      $('#id_slug').val(slugifiedTitle);
    }
  });
}

window.initSlugAutoPopulate = initSlugAutoPopulate;

function initSlugCleaning() {
  // eslint-disable-next-line func-names
  $('#id_slug').on('blur', function () {
    // if a user has just set the slug themselves, don't remove stop words etc, just illegal characters
    $(this).val(cleanForSlug($(this).val(), false));
  });
}

window.initSlugCleaning = initSlugCleaning;

function initErrorDetection() {
  const errorSections = {};

  // first count up all the errors
  // eslint-disable-next-line func-names
  $('.error-message,.help-critical').each(function () {
    const parentSection = $(this).closest('section');

    if (!errorSections[parentSection.attr('id')]) {
      errorSections[parentSection.attr('id')] = 0;
    }

    errorSections[parentSection.attr('id')] =
      errorSections[parentSection.attr('id')] + 1;
  });

  // now identify them on each tab
  // eslint-disable-next-line guard-for-in
  for (const index in errorSections) {
    $('[data-tabs] a[href="#' + index + '"]')
      .find('[data-tabs-errors]')
      .addClass('!w-flex')
      .find('[data-tabs-errors-count]')
      .text(errorSections[index]);
  }
}

window.initErrorDetection = initErrorDetection;

function initKeyboardShortcuts() {
  // eslint-disable-next-line no-undef
  Mousetrap.bind(['mod+p'], () => {
    const previewToggle = document.querySelector(
      '[data-side-panel-toggle="preview"]',
    );
    if (previewToggle) previewToggle.click();
    return false;
  });

  // eslint-disable-next-line no-undef
  Mousetrap.bind(['mod+s'], () => {
    $('.action-save').trigger('click');
    return false;
  });
}

window.initKeyboardShortcuts = initKeyboardShortcuts;

$(() => {
  /* Only non-live pages should auto-populate the slug from the title */
  if (!$('body').hasClass('page-is-live')) {
    initSlugAutoPopulate();
  }

  initSlugCleaning();
  initErrorDetection();
  initKeyboardShortcuts();
});

let updateFooterTextTimeout = -1;
window.updateFooterSaveWarning = (formDirty, commentsDirty) => {
  const warningContainer = $('[data-unsaved-warning]');
  const warnings = warningContainer.find('[data-unsaved-type]');
  const anyDirty = formDirty || commentsDirty;
  const typeVisibility = {
    all: formDirty && commentsDirty,
    any: anyDirty,
    comments: commentsDirty && !formDirty,
    edits: formDirty && !commentsDirty,
  };

  let hiding = false;
  if (anyDirty) {
    warningContainer.removeClass('footer__container--hidden');
  } else {
    if (!warningContainer.hasClass('footer__container--hidden')) {
      hiding = true;
    }
    warningContainer.addClass('footer__container--hidden');
  }
  clearTimeout(updateFooterTextTimeout);
  const updateWarnings = () => {
    for (const warning of warnings) {
      const visible = typeVisibility[warning.dataset.unsavedType];
      warning.hidden = !visible;
    }
  };
  if (hiding) {
    // If hiding, we want to keep the text as-is before it disappears
    updateFooterTextTimeout = setTimeout(updateWarnings, 1050);
  } else {
    updateWarnings();
  }
};

document.addEventListener('DOMContentLoaded', () => {
  const setPanel = (panelName) => {
    const sidePanelWrapper = document.querySelector('[data-form-side]');
    const body = document.querySelector('body');
    // Open / close side panel

    // HACK: For now, the comments will show without the side-panel opening.
    // They will later be updated so that they render inside the side panel.
    // We couldn't implement this for Wagtail 3.0 as the existing field styling
    // renders the "Add comment" button on the right hand side, and this gets
    // covered up by the side panel.

    if (panelName === '' || panelName === 'comments') {
      sidePanelWrapper.classList.remove('form-side--open');
      sidePanelWrapper.removeAttribute('aria-labelledby');
    } else {
      sidePanelWrapper.classList.add('form-side--open');
      sidePanelWrapper.setAttribute(
        'aria-labelledby',
        `side-panel-${panelName}-title`,
      );
    }

    document.querySelectorAll('[data-side-panel]').forEach((panel) => {
      if (panel.dataset.sidePanel === panelName) {
        if (panel.hidden) {
          // eslint-disable-next-line no-param-reassign
          panel.hidden = false;
          panel.dispatchEvent(new CustomEvent('show'));
          body.classList.add('side-panel-open');
        }
      } else if (!panel.hidden) {
        // eslint-disable-next-line no-param-reassign
        panel.hidden = true;
        panel.dispatchEvent(new CustomEvent('hide'));
        body.classList.remove('side-panel-open');
      }
    });

    // Update aria-expanded attribute on the panel toggles
    document.querySelectorAll('[data-side-panel-toggle]').forEach((toggle) => {
      toggle.setAttribute(
        'aria-expanded',
        toggle.dataset.sidePanelToggle === panelName ? 'true' : 'false',
      );
    });
  };

  const togglePanel = (panelName) => {
    const isAlreadyOpen = !document
      .querySelector(`[data-side-panel="${panelName}"]`)
      .hasAttribute('hidden');

    if (isAlreadyOpen) {
      // Close the sidebar
      setPanel('');
    } else {
      // Open the sidebar / navigate to the panel
      setPanel(panelName);
    }
  };

  document.querySelectorAll('[data-side-panel-toggle]').forEach((toggle) => {
    toggle.addEventListener('click', () => {
      togglePanel(toggle.dataset.sidePanelToggle);
    });
  });

  const closeButton = document.querySelector('[data-form-side-close-button]');
  if (closeButton instanceof HTMLButtonElement) {
    closeButton.addEventListener('click', () => {
      setPanel('');
    });
  }
});
