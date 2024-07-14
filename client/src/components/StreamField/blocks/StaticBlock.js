import { escapeHtml as h } from '../../../utils/text';
import {
  DeleteButton,
  DuplicateButton,
  MoveDownButton,
  MoveUpButton,
} from './BaseSequenceBlock';

export class StaticBlock {
  constructor(blockDef, placeholder) {
    this.blockDef = blockDef;

    const element = document.createElement('div');

    if (this.blockDef.meta.html) {
      element.innerHTML = this.blockDef.meta.html;
    } else {
      element.innerHTML = h(this.blockDef.meta.text);
    }

    placeholder.replaceWith(element);
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setState(_state) {}

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setError(_errorList) {}

  getState() {
    return null;
  }

  getValue() {
    return null;
  }

  focus() {}
}

export class StaticBlockDefinition {
  constructor(name, meta) {
    this.name = name;
    this.meta = meta;
  }

  render(placeholder) {
    return new StaticBlock(this, placeholder);
  }

  setActions(base) {
    base.addActionButton(new MoveUpButton(base));
    base.addActionButton(new MoveDownButton(base));
    base.addActionButton(new DuplicateButton(base));
    base.addActionButton(new DeleteButton(base));
  }
}
