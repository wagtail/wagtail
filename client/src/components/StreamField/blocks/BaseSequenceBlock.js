/* global $ */

export class BaseSequenceChild {
  constructor(blockDef, placeholder, prefix, index, id, initialState, opts) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;
    this.index = index;
    this.id = id;

    const animate = opts && opts.animate;
    this.onRequestDelete = opts && opts.onRequestDelete;

    const dom = $(`
      <div aria-hidden="false">
        <input type="hidden"  name="${this.prefix}-deleted" value="">
        <input type="hidden" name="${this.prefix}-order" value="${index}">
        <input type="hidden" name="${this.prefix}-type" value="${this.type}">
        <input type="hidden" name="${this.prefix}-id" value="${this.id || ''}">

        <div>
          <div class="c-sf-container__block-container">
            <div class="c-sf-block">
              <div class="c-sf-block__header">
                <span class="c-sf-block__header__icon">
                  <i class="icon icon-${this.blockDef.meta.icon}"></i>
                </span>
                <h3 class="c-sf-block__header__title"></h3>
                <div class="c-sf-block__actions">
                  <span class="c-sf-block__type">${this.blockDef.meta.label}</span>
                  <button type="button" data-move-up-button class="c-sf-block__actions__single"
                      disabled title="{% trans 'Move up' %}">
                    <i class="icon icon-arrow-up" aria-hidden="true"></i>
                  </button>
                  <button type="button" data-move-down-button class="c-sf-block__actions__single"
                      disabled title="{% trans 'Move down' %}">
                    <i class="icon icon-arrow-down" aria-hidden="true"></i>
                  </button>
                  <button type="button" data-delete-button
                      class="c-sf-block__actions__single" title="{% trans 'Delete' %}">
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

    dom.find('button[data-delete-button]').click(() => {
      if (this.onRequestDelete) this.onRequestDelete(this.index);
    });

    this.deletedInput = dom.find(`input[name="${this.prefix}-deleted"]`);
    this.indexInput = dom.find(`input[name="${this.prefix}-order"]`);

    this.moveUpButton = dom.find('button[data-move-up-button]');
    this.moveDownButton = dom.find('button[data-move-down-button]');

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
