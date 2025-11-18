import { gettext } from '../../../utils/gettext';
import { escapeHtml as h } from '../../../utils/text';
import type { BaseSequenceChild } from './BaseSequenceBlock';

export abstract class ActionButton {
  declare enableEvent?: string;
  declare disableEvent?: string;
  declare initiallyDisabled?: boolean;
  declare icon: string;
  declare labelIdentifier: string;
  declare label: string;

  declare sequenceChild: BaseSequenceChild;
  declare dom: JQuery<HTMLElement>;

  abstract onClick?(): void;

  constructor(sequenceChild: BaseSequenceChild) {
    this.sequenceChild = sequenceChild;
  }

  render(container) {
    this.dom = $(`
      <button type="button" class="button button--icon text-replace white" data-streamfield-action="${this.labelIdentifier}" title="${h(this.label)}">
        <svg class="icon icon-${h(this.icon)}" aria-hidden="true">
          <use href="#icon-${h(this.icon)}"></use>
        </svg>
      </button>
    `);

    this.dom.on('click', () => {
      if (this.onClick) this.onClick();
      return false; // don't propagate to header's onclick event (which collapses the block)
    });

    $(container).append(this.dom);

    if (this.enableEvent) {
      this.sequenceChild.addEventListener(this.enableEvent, () => {
        this.enable();
      });
    }

    if (this.disableEvent) {
      this.sequenceChild.addEventListener(this.disableEvent, () => {
        this.disable();
      });
    }

    if (this.initiallyDisabled) {
      this.disable();
    }
  }

  enable() {
    this.dom.removeAttr('disabled');
  }

  disable() {
    this.dom.attr('disabled', 'true');
  }
}

export class MoveUpButton extends ActionButton {
  enableEvent = 'enableMoveUp';
  disableEvent = 'disableMoveUp';
  initiallyDisabled = true;
  icon = 'arrow-up';
  labelIdentifier = 'MOVE_UP';
  label = gettext('Move up');

  onClick() {
    this.sequenceChild.moveUp();
  }
}

export class MoveDownButton extends ActionButton {
  enableEvent = 'enableMoveDown';
  disableEvent = 'disableMoveDown';
  initiallyDisabled = true;
  icon = 'arrow-down';
  labelIdentifier = 'MOVE_DOWN';
  label = gettext('Move down');

  onClick() {
    this.sequenceChild.moveDown();
  }
}

export class DragButton extends ActionButton {
  enableEvent = 'enableDrag';
  disableEvent = 'disableDrag';
  initiallyDisabled = false;
  icon = 'grip';
  labelIdentifier = 'DRAG';
  label = gettext('Drag');
  onClick = undefined;
}

export class DuplicateButton extends ActionButton {
  enableEvent = 'enableDuplication';
  disableEvent = 'disableDuplication';
  icon = 'copy';
  labelIdentifier = 'DUPLICATE';
  label = gettext('Duplicate');

  onClick() {
    this.sequenceChild.duplicate({ animate: true });
  }
}

export class DeleteButton extends ActionButton {
  icon = 'bin';
  labelIdentifier = 'DELETE';
  label = gettext('Delete');

  onClick() {
    this.sequenceChild.delete({ animate: true });
  }
}
