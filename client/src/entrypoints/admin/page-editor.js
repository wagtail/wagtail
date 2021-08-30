import $ from 'jquery';
import { cleanForSlug } from '../../utils/cleanForSlug';

window.halloPlugins = {};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function registerHalloPlugin(name, opts) {  // lgtm[js/unused-local-variable]
  /* Obsolete - used on Wagtail <1.12 to register plugins for the hallo.js editor.
  Defined here so that third-party plugins can continue to call it to provide Wagtail <1.12
  compatibility, without throwing an error on later versions. */
}
window.registerHalloPlugin = registerHalloPlugin;

function InlinePanel(opts) {  // lgtm[js/unused-local-variable]
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
      $('#' + childId).addClass('deleted').slideUp(() => {
        self.updateMoveButtonDisabledStates();
        self.updateAddButtonState();
        self.setHasContent();
      });
    });

    if (opts.canOrder) {
      $('#' + prefix + '-move-up').on('click', () => {
        const currentChild = $('#' + childId);
        const currentChildOrderElem = currentChild.children('input[name$="-ORDER"]');
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
        const currentChildOrderElem = currentChild.children('input[name$="-ORDER"]');
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
      $('#' + childId).addClass('deleted').hide(0, () => {
        self.updateMoveButtonDisabledStates();
        self.updateAddButtonState();
        self.setHasContent();
      });

      $('#' + childId).find('.error-message').remove();
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
      const forms = $('> [data-inline-panel-child]', self.formsUl).not('.deleted');
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

    // eslint-disable-next-line func-names
    children.each(function () {
      $(this).css('top', $(this).position().top);
    }).addClass('moving');

    // animate swapping around
    item1.animate({
      top: item2.position().top
    }, 200, () => {
      parent.removeClass('moving').removeAttr('style');
      children.removeClass('moving').removeAttr('style');
    });

    item2.animate({
      top: item1.position().top
    }, 200, () => {
      parent.removeClass('moving').removeAttr('style');
      children.removeClass('moving').removeAttr('style');
    });
  };

  // eslint-disable-next-line no-undef
  buildExpandingFormset(opts.formsetPrefix, {
    onAdd(formCount) {
      const newChildPrefix = opts.emptyChildFormPrefix.replace(/__prefix__/g, formCount);
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
    }
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
    slugFollowsTitle = (currentSlug === slugifiedTitle);
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

    errorSections[parentSection.attr('id')] = errorSections[parentSection.attr('id')] + 1;
  });

  // now identify them on each tab
  // eslint-disable-next-line no-restricted-syntax, guard-for-in
  for (const index in errorSections) {
    $('[data-tab-nav] a[href="#' + index + '"]').addClass('errors').attr('data-count', errorSections[index]);
  }
}
window.initErrorDetection = initErrorDetection;

function initKeyboardShortcuts() {
  // eslint-disable-next-line no-undef
  Mousetrap.bind(['mod+p'], () => {
    $('.action-preview').trigger('click');
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

  //
  // Preview
  //
  // In order to make the preview truly reliable, the preview page needs
  // to be perfectly independent from the edit page,
  // from the browser perspective. To pass data from the edit page
  // to the preview page, we send the form after each change
  // and save it inside the user session.

  const $previewButton = $('.action-preview');
  const $form = $('#page-edit-form');
  const previewUrl = $previewButton.data('action');
  let autoUpdatePreviewDataTimeout = -1;

  function setPreviewData() {
    return $.ajax({
      url: previewUrl,
      method: 'POST',
      data: new FormData($form[0]),
      processData: false,
      contentType: false
    });
  }

  $previewButton.one('click', () => {
    if ($previewButton.data('auto-update')) {
      // Form data is changed when field values are changed
      // (change event), when HTML elements are added, modified, moved,
      // and deleted (DOMSubtreeModified event), and we need to delay
      // setPreviewData when typing to avoid useless extra AJAX requests
      // (so we postpone setPreviewData when keyup occurs).
      // eslint-disable-next-line no-warning-comments
      // TODO: Replace DOMSubtreeModified with a MutationObserver.
      $form.on('change keyup DOMSubtreeModified', () => {
        clearTimeout(autoUpdatePreviewDataTimeout);
        autoUpdatePreviewDataTimeout = setTimeout(setPreviewData, 1000);
      }).trigger('change');
    }
  });

  // eslint-disable-next-line func-names
  $previewButton.on('click', function (e) {
    e.preventDefault();
    const $this = $(this);
    const $icon = $this.filter('.icon');
    const thisPreviewUrl = $this.data('action');
    $icon.addClass('icon-spinner').removeClass('icon-view');
    const previewWindow = window.open('', thisPreviewUrl);
    previewWindow.focus();

    setPreviewData().done((data) => {
      if (data.is_valid) {
        previewWindow.document.location = thisPreviewUrl;
      } else {
        window.focus();
        previewWindow.close();
        // eslint-disable-next-line no-warning-comments
        // TODO: Stop sending the form, as it removes file data.
        $form.trigger('submit');
      }
    }).fail(() => {
      // eslint-disable-next-line no-alert
      alert('Error while sending preview data.');
      window.focus();
      previewWindow.close();
    })
      .always(() => {
        $icon.addClass('icon-view').removeClass('icon-spinner');
      });
  });
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
    edits: formDirty && !commentsDirty
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
