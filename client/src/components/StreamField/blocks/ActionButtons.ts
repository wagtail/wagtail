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

  declare sequenceChild?: BaseSequenceChild;
  declare dom: JQuery<HTMLElement>;

  abstract onClick?(): void;

  constructor(sequenceChild?: BaseSequenceChild) {
    this.sequenceChild = sequenceChild;
  }

  render(container, position = 'after') {
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

    if (position === 'after') {
      $(container).append(this.dom);
    } else {
      $(container).prepend(this.dom);
    }

    if (this.enableEvent) {
      this.sequenceChild!.addEventListener(this.enableEvent, () => {
        this.enable();
      });
    }

    if (this.disableEvent) {
      this.sequenceChild!.addEventListener(this.disableEvent, () => {
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
    this.sequenceChild!.moveUp();
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
    this.sequenceChild!.moveDown();
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
    this.sequenceChild!.duplicate({ animate: true });
  }
}

export class DeleteButton extends ActionButton {
  icon = 'bin';
  labelIdentifier = 'DELETE';
  label = gettext('Delete');

  onClick() {
    this.sequenceChild!.delete({ animate: true });
  }
}

export class SettingsButton extends ActionButton {
  icon = 'cog';
  labelIdentifier = 'SETTINGS';
  label = gettext('Settings');

  constructor(public settingsPanel: HTMLElement) {
    // Normally, ActionButton subclasses expect a BaseSequenceChild instance.
    // However, SettingsButton doesn't need it, as it can work with any object
    // that has the collapsible panel.
    super();
  }

  render(container: any, position = 'before'): void {
    super.render(container, position);
    const { id } = this.settingsPanel;
    this.dom.attr('aria-expanded', 'false');
    this.dom.attr('aria-controls', id);
    this.dom.append(/* html */ `
      <div
        class="w-badge w-badge--critical w-hidden"
        data-controller="w-count"
        data-w-count-active-class="!w-flex"
        data-w-count-container-value="#${id}"
      >
        <span aria-hidden="true" data-w-count-target="total"></span>
        <span class="w-sr-only">(<span data-w-count-target="label"></span>)</span>
      </div>
    `);
    this.settingsPanel.addEventListener('beforematch', () => this.toggle(true));
  }

  toggle(open?: boolean) {
    const parentPanel = this.settingsPanel.closest('[data-panel]')!;
    const parentToggle = parentPanel.querySelector<HTMLButtonElement>(
      '[data-panel-toggle]',
    )!;

    let isExpanding = open ?? this.dom.attr('aria-expanded') === 'false';
    if (parentToggle.getAttribute('aria-expanded') === 'false') {
      // If the parent panel is currently collapsed, we cannot see the effect of
      // toggling settings visibility, so first expand the panel.
      parentToggle.click();
      // However, if the settings were previously shown, toggling its visibility
      // will now hide it, which could be confusing, so just force it to show.
      isExpanding = true;
    }

    if (isExpanding) {
      this.dom.attr('aria-expanded', 'true');
      this.settingsPanel.removeAttribute('hidden');
    } else {
      this.dom.attr('aria-expanded', 'false');
      const hidden = 'onbeforematch' in document.body ? 'until-found' : '';
      this.settingsPanel.setAttribute('hidden', hidden);
    }
  }

  onClick() {
    this.toggle();
  }
}
