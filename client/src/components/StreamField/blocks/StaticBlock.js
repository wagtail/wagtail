import { escapeHtml as h } from '../../../utils/text';

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

  // eslint-disable-next-line @typescript-eslint/no-unused-vars, @typescript-eslint/no-empty-function
  setState(_state) {}

  // eslint-disable-next-line @typescript-eslint/no-unused-vars, @typescript-eslint/no-empty-function
  setError(_errorList) {}

  getState() {
    return null;
  }

  getValue() {
    return null;
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
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
}
