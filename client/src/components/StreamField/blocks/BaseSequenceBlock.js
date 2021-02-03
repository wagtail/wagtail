/* global $ */

import { escapeHtml as h } from '../../../utils/text';

export class BaseSequenceChild {
  constructor(blockDef, placeholder, prefix, index, id, initialState, opts) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;
    this.index = index;
    this.id = id;

    const animate = opts && opts.animate;
    this.onRequestDuplicate = opts && opts.onRequestDuplicate;
    this.onRequestDelete = opts && opts.onRequestDelete;
    this.onRequestMoveUp = opts && opts.onRequestMoveUp;
    this.onRequestMoveDown = opts && opts.onRequestMoveDown;
    const strings = (opts && opts.strings) || {};

    const dom = $(`
      <div aria-hidden="false">
        <input type="hidden"  name="${this.prefix}-deleted" value="">
        <input type="hidden" name="${this.prefix}-order" value="${index}">
        <input type="hidden" name="${this.prefix}-type" value="${h(this.type || '')}">
        <input type="hidden" name="${this.prefix}-id" value="${h(this.id || '')}">

        <div>
          <div class="c-sf-container__block-container">
            <div class="c-sf-block">
              <div class="c-sf-block__header">
                <span class="c-sf-block__header__icon">
                  <i class="icon icon-${h(this.blockDef.meta.icon)}"></i>
                </span>
                <h3 class="c-sf-block__header__title"></h3>
                <div class="c-sf-block__actions">
                  <span class="c-sf-block__type">${h(this.blockDef.meta.label)}</span>
                  <button type="button" data-move-up-button class="c-sf-block__actions__single"
                      disabled title="${h(strings.MOVE_UP)}">
                    <i class="icon icon-arrow-up" aria-hidden="true"></i>
                  </button>
                  <button type="button" data-move-down-button class="c-sf-block__actions__single"
                      disabled title="${h(strings.MOVE_DOWN)}">
                    <i class="icon icon-arrow-down" aria-hidden="true"></i>
                  </button>
                  <button type="button" data-duplicate-button
                      class="c-sf-block__actions__single" title="${h(strings.DUPLICATE)}">
                    <i class="icon icon-duplicate" aria-hidden="true"></i>
                  </button>
                  <button type="button" data-delete-button
                      class="c-sf-block__actions__single" title="${h(strings.DELETE)}">
                    <i class="icon icon-bin" aria-hidden="true"></i>
                  </button>
                </div>
              </div>
              <div class="c-sf-block__content" aria-hidden="false">
                <div class="c-sf-block__content-inner">
                  <div data-streamfield-block></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `);

    $(placeholder).replaceWith(dom);
    this.element = dom.get(0);
    const blockElement = dom.find('[data-streamfield-block]').get(0);

    dom.find('button[data-duplicate-button]').click(() => {
      if (this.onRequestDuplicate) this.onRequestDuplicate(this.index);
    });

    dom.find('button[data-delete-button]').click(() => {
      if (this.onRequestDelete) this.onRequestDelete(this.index);
    });

    this.deletedInput = dom.find(`input[name="${this.prefix}-deleted"]`);
    this.indexInput = dom.find(`input[name="${this.prefix}-order"]`);

    this.moveUpButton = dom.find('button[data-move-up-button]');
    this.moveUpButton.click(() => {
      if (this.onRequestMoveUp) this.onRequestMoveUp(this.index);
    });
    this.moveDownButton = dom.find('button[data-move-down-button]');
    this.moveDownButton.click(() => {
      if (this.onRequestMoveDown) this.onRequestMoveDown(this.index);
    });

    this.block = this.blockDef.render(blockElement, this.prefix + '-value', initialState);

    if (animate) {
      dom.hide().slideDown();
    }
  }

  markDeleted({ animate = false }) {
    this.deletedInput.val('1');
    if (animate) {
      $(this.element).slideUp().dequeue()
        .fadeOut()
        .attr('aria-hidden', 'true');
    } else {
      $(this.element).hide().attr('aria-hidden', 'true');
    }
  }

  enableMoveUp() {
    this.moveUpButton.removeAttr('disabled');
  }
  disableMoveUp() {
    this.moveUpButton.attr('disabled', 'true');
  }
  enableMoveDown() {
    this.moveDownButton.removeAttr('disabled');
  }
  disableMoveDown() {
    this.moveDownButton.attr('disabled', 'true');
  }

  setIndex(newIndex) {
    this.index = newIndex;
    this.indexInput.val(newIndex);
  }

  setError(error) {
    this.block.setError(error);
  }

  focus() {
    this.block.focus();
  }
}

export class BaseInsertionControl {
  /* Base class for controls that appear between blocks in a sequence, to allow inserting new
  blocks at that point. Subclasses should render an HTML structure with a single root element
  (replacing the placeholder passed to the constructor) and set it as this.element.
  When the user requests to insert a block, we call onRequestInsert passing the index number
  and a dict of control-specific options. */
  constructor(placeholder, opts) {
    this.index = opts && opts.index;
    this.onRequestInsert = opts && opts.onRequestInsert;
  }

  setIndex(newIndex) {
    this.index = newIndex;
  }

  delete() {
    $(this.element).hide().attr('aria-hidden', 'true');
  }
}
