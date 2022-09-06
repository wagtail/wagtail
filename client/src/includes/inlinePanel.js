import $ from 'jquery';
import { initCollapsiblePanels } from './panels';

// eslint-disable-next-line prefer-destructuring
const buildExpandingFormset = window.buildExpandingFormset;

/**
 * Attaches behaviour for an InlinePanel where inner panels can be created,
 * removed and re-ordered.
 *
 * @param {Object} opts
 * @param {string} opts.formsetPrefix
 * @param {boolean?} opts.canOrder
 * @param {string} opts.emptyChildFormPrefix
 * @param {number} opts.maxForms
 * @param {function} opts.onAdd
 * @returns {Object}
 */
function inlinePanel(opts) {
  const self = {};

  self.initChildControls = function initChildControls(prefix) {
    const childId = 'inline_child_' + prefix;
    const deleteInputId = 'id_' + prefix + '-DELETE';
    const currentChild = $('#' + childId);
    const $up = currentChild.find('[data-inline-panel-child-move-up]');
    const $down = currentChild.find('[data-inline-panel-child-move-down]');

    $('#' + deleteInputId + '-button').on('click', () => {
      /* set 'deleted' form field to true */
      $('#' + deleteInputId).val('1');
      currentChild.addClass('deleted').slideUp(() => {
        self.updateMoveButtonDisabledStates();
        self.updateAddButtonState();
      });
    });

    if (opts.canOrder) {
      $up.on('click', () => {
        const currentChildOrderElem = currentChild.find(
          `input[name="${prefix}-ORDER"]`,
        );
        const currentChildOrder = currentChildOrderElem.val();

        /* find the previous visible 'inline_child' li before this one */
        const prevChild = currentChild.prevAll(':not(.deleted)').first();
        if (!prevChild.length) return;
        const prevChildPrefix = prevChild[0].id.replace('inline_child_', '');
        const prevChildOrderElem = prevChild.find(
          `input[name="${prevChildPrefix}-ORDER"]`,
        );
        const prevChildOrder = prevChildOrderElem.val();

        // async swap animation must run before the insertBefore line below, but doesn't need to finish first
        self.animateSwap(currentChild, prevChild);

        currentChild.insertBefore(prevChild);
        currentChildOrderElem.val(prevChildOrder);
        prevChildOrderElem.val(currentChildOrder);

        self.updateMoveButtonDisabledStates();
      });

      $down.on('click', () => {
        const currentChildOrderElem = currentChild.find(
          `input[name="${prefix}-ORDER"]`,
        );
        const currentChildOrder = currentChildOrderElem.val();

        /* find the next visible 'inline_child' li after this one */
        const nextChild = currentChild.nextAll(':not(.deleted)').first();
        if (!nextChild.length) return;
        const nextChildPrefix = nextChild[0].id.replace('inline_child_', '');
        const nextChildOrderElem = nextChild.find(
          `input[name="${nextChildPrefix}-ORDER"]`,
        );
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
        });

      $('#' + childId)
        .find('.error-message')
        .remove();
    }
  };

  self.formsElt = $('#' + opts.formsetPrefix + '-FORMS');

  self.updateMoveButtonDisabledStates = function updateMoveButtons() {
    if (opts.canOrder) {
      const forms = self.formsElt.children(':not(.deleted)');
      forms.each(function updateButtonStates(i) {
        const isFirst = i === 0;
        const isLast = i === forms.length - 1;
        $('[data-inline-panel-child-move-up]', this).prop('disabled', isFirst);
        $('[data-inline-panel-child-move-down]', this).prop('disabled', isLast);
      });
    }
  };

  self.updateAddButtonState = function updateAddButtonState() {
    if (opts.maxForms) {
      const forms = $('> [data-inline-panel-child]', self.formsElt).not(
        '.deleted',
      );
      const addButton = $('#' + opts.formsetPrefix + '-ADD');

      if (forms.length >= opts.maxForms) {
        addButton.prop('disabled', true);
      } else {
        addButton.prop('disabled', false);
      }
    }
  };

  self.animateSwap = function animateSwap(item1, item2) {
    const parent = self.formsElt;
    const children = parent.children(':not(.deleted)');

    // Position children absolutely and add hard-coded height
    // to prevent scroll jumps when reordering.
    parent.css({
      position: 'relative',
      height: parent.height(),
    });

    children
      .each(function moveChildTop() {
        $(this).css('top', $(this).position().top);
      })
      .css({
        // Set this after the actual position so the items animate correctly.
        position: 'absolute',
        width: '100%',
      });

    // animate swapping around
    item1.animate(
      {
        top: item2.position().top,
      },
      200,
      () => {
        parent.removeAttr('style');
        children.removeAttr('style');
      },
    );

    item2.animate(
      {
        top: item1.position().top,
      },
      200,
      () => {
        parent.removeAttr('style');
        children.removeAttr('style');
      },
    );
  };

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
      initCollapsiblePanels(
        document.querySelectorAll(
          `#inline_child_${newChildPrefix} [data-panel-toggle]`,
        ),
      );

      if (opts.onAdd) opts.onAdd();
    },
  });

  return self;
}

export { inlinePanel };
