import $ from 'jquery';
import { cleanForSlug } from '../../utils/text';
import { InlinePanel } from '../../components/InlinePanel';
import { ngettext } from '../../utils/gettext';

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
  $('.error-message,.help-critical').each(function collectError() {
    const parentSection = $(this).closest('section[role="tabpanel"]');

    if (!errorSections[parentSection.attr('id')]) {
      errorSections[parentSection.attr('id')] = 0;
    }

    errorSections[parentSection.attr('id')] =
      errorSections[parentSection.attr('id')] + 1;
  });

  // now identify them on each tab
  Object.entries(errorSections).forEach(([sectionId, errorCount]) => {
    const tabErrorsElement = $(`[data-tabs] a[href="#${sectionId}"]`).find(
      '[data-tabs-errors]',
    );

    // show and add error count
    tabErrorsElement
      .addClass('!w-flex')
      .find('[data-tabs-errors-count]')
      .text(errorCount);

    // update label for screen readers
    tabErrorsElement
      .find('[data-tabs-errors-statement]')
      .text(
        ngettext(
          '(%(errorCount)s error)',
          '(%(errorCount)s errors)',
          errorCount,
        ).replace('%(errorCount)s', errorCount),
      );
  });
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
    warnings.each((_, warning) => {
      const visible = typeVisibility[warning.dataset.unsavedType];
      // eslint-disable-next-line no-param-reassign
      warning.hidden = !visible;
    });
  };
  if (hiding) {
    // If hiding, we want to keep the text as-is before it disappears
    updateFooterTextTimeout = setTimeout(updateWarnings, 1050);
  } else {
    updateWarnings();
  }
};
