import $ from 'jquery';
import Sortable from 'sortablejs';
import { initCollapsiblePanels } from '../../includes/panels';
import { ExpandingFormset } from '../ExpandingFormset';

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
export class InlinePanel extends ExpandingFormset {
  constructor(opts) {
    super(opts.formsetPrefix, opts);
    this.formsElt = $('#' + opts.formsetPrefix + '-FORMS');

    if (this.opts.canOrder) {
      this.sortable = Sortable.create(this.formsElt.get(0), {
        handle: '[data-inline-panel-child-drag]',
        animation: 200,
        onEnd: this.handleDragEnd.bind(this),
        setData: (dataTransfer) => {
          dataTransfer.setData(
            'application/vnd.wagtail.type',
            'inlinepanel-child',
          );
        },
      });
    }

    for (let i = 0; i < this.formCount; i += 1) {
      const childPrefix = this.opts.emptyChildFormPrefix.replace(
        /__prefix__/g,
        i,
      );
      this.initChildControls(childPrefix);
    }

    this.updateControlStates();
    // dispatch event for form ready
    setTimeout(() => {
      this.formsElt.get(0)?.dispatchEvent(
        new CustomEvent('w-formset:ready', {
          bubbles: true,
          cancelable: false,
          detail: { ...opts },
        }),
      );
    });
  }

  /**
   * Update states of listing controls in response to a change of state such as
   * adding, deleting or moving an element.
   */
  updateControlStates() {
    this.updateChildCount();
    this.updateMoveButtonDisabledStates();
    this.updateAddButtonState();
  }

  initChildControls(prefix) {
    const childId = 'inline_child_' + prefix;
    const deleteInputId = 'id_' + prefix + '-DELETE';
    const currentChild = $('#' + childId);
    const $up = currentChild.find('[data-inline-panel-child-move-up]:first ');
    const $down = currentChild.find(
      '[data-inline-panel-child-move-down]:first ',
    );

    $('#' + deleteInputId + '-button').on('click', () => {
      /* set 'deleted' form field to true */
      $('#' + deleteInputId)
        .val('1')
        .get(0)
        .dispatchEvent(new Event('change', { bubbles: true }));
      currentChild.addClass('deleted').slideUp(() => {
        this.updateControlStates();
        // dispatch event for deleting form
        currentChild.get(0).dispatchEvent(
          new CustomEvent('w-formset:removed', {
            bubbles: true,
            cancelable: false,
            detail: { ...this.opts },
          }),
        );
      });
    });

    if (this.opts.canOrder) {
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
        this.animateSwap(currentChild, prevChild);

        currentChild.insertBefore(prevChild);
        currentChildOrderElem.val(prevChildOrder);
        prevChildOrderElem.val(currentChildOrder);

        this.updateControlStates();
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
        this.animateSwap(currentChild, nextChild);

        currentChild.insertAfter(nextChild);
        currentChildOrderElem.val(nextChildOrder);
        nextChildOrderElem.val(currentChildOrder);

        this.updateControlStates();
      });
    }

    /* Hide container on page load if it is marked as deleted. Remove the error
    message so that it doesn't count towards the number of errors on the tab at the
    top of the page. */
    if ($('#' + deleteInputId).val() === '1') {
      $('#' + childId)
        .addClass('deleted')
        .hide(0, () => {
          this.updateControlStates();
        });

      $('#' + childId)
        .find('.error-message')
        .remove();
    }
  }

  updateMoveButtonDisabledStates() {
    if (this.opts.canOrder) {
      const forms = this.formsElt.children(':not(.deleted)');
      forms.each(function updateButtonStates(i) {
        const isFirst = i === 0;
        const isLast = i === forms.length - 1;
        $('[data-inline-panel-child-move-up]:first', this).prop(
          'disabled',
          isFirst,
        );
        $('[data-inline-panel-child-move-down]:first', this).prop(
          'disabled',
          isLast,
        );
      });
    }
  }

  /**
   * Adds the child’s count next to its heading label, ignoring deleted items.
   */
  updateChildCount() {
    const forms = this.formsElt.children(':not(.deleted)');
    forms.each(function updateCountState(i) {
      $('[data-inline-panel-child-count]', this)
        .first()
        .text(` ${i + 1}`);
    });
  }

  getChildCount() {
    const forms = $('> [data-inline-panel-child]', this.formsElt).not(
      '.deleted',
    );
    return forms.length;
  }

  updateAddButtonState() {
    if (this.opts.maxForms) {
      const addButton = $('#' + this.opts.formsetPrefix + '-ADD');

      if (this.getChildCount() >= this.opts.maxForms) {
        addButton.prop('disabled', true);
      } else {
        addButton.prop('disabled', false);
      }
    }
  }

  animateSwap(item1, item2) {
    const parent = this.formsElt;
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
  }

  /**
   * Add tabindex -1 into newly created form if attr not present and
   * remove attr from old forms on blur event, if not present previously.
   * Always scroll and then focus on the element.
   */
  initialFocus($node) {
    if (!$node || !$node.length) return;

    // If element does not already have tabindex, set it
    // then ensure we remove after blur (when it loses focus).
    if (!$node.attr('tabindex')) {
      $node.attr('tabindex', -1);
      $node.one('blur', () => {
        if ($node.attr('tabindex') === '-1') {
          $node.removeAttr('tabindex');
        }
      });
    }

    $node[0].scrollIntoView({ behavior: 'smooth' });
    $node.focus();
  }

  addForm(opts = {}) {
    /*
    Supported opts:
    runCallbacks (default: true) - if false, the onAdd and onInit callbacks will not be run
    */

    // don't run callbacks yet - we'll do that after initialising InlinePanel's controls
    super.addForm({ runCallbacks: false });

    // formCount has now been incremented, so subtract one to get back the 0-based index
    // of the newly added form
    const formIndex = this.formCount - 1;

    const newChildPrefix = this.opts.emptyChildFormPrefix.replace(
      /__prefix__/g,
      formIndex,
    );
    this.initChildControls(newChildPrefix);
    if (this.opts.canOrder) {
      /* ORDER values are 1-based, so need to add 1 to formIndex */
      $('#id_' + newChildPrefix + '-ORDER')
        .val(formIndex + 1)
        .get(0)
        .dispatchEvent(new Event('change', { bubbles: true }));
    }

    this.updateControlStates();
    initCollapsiblePanels(
      document.querySelectorAll(
        `#inline_child_${newChildPrefix} [data-panel-toggle]`,
      ),
    );

    if (!('runCallbacks' in opts) || opts.runCallbacks) {
      if (this.opts.onAdd) this.opts.onAdd(formIndex);
      if (this.opts.onInit) this.opts.onInit(formIndex);
    }

    this.initialFocus($(`#inline_child_${newChildPrefix}-panel-content`));

    const newChild = this.formsElt.children().last().get(0);
    if (!newChild) return;

    // dispatch event for initialising a form
    newChild.dispatchEvent(
      new CustomEvent('w-formset:added', {
        bubbles: true,
        cancelable: false,
        detail: { formIndex, ...this.opts },
      }),
    );
  }

  /**
   * Update fields based on the current DOM order.
   */
  updateOrderValues() {
    const forms = this.formsElt.children(':not(.deleted)');
    forms.each((index, form) => {
      const prefix = form.id.replace('inline_child_', '');
      const orderInput = $(form).find(`[name="${prefix}-ORDER"]`);
      orderInput.val(index + 1);
    });
  }

  handleDragEnd(e) {
    const { oldIndex, newIndex } = e;
    if (oldIndex !== newIndex) {
      this.updateOrderValues();
      this.updateControlStates();
    }
  }
}
