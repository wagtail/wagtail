/* global $ */

import { escapeHtml as h } from '../../../utils/text';
import { hasOwn } from '../../../utils/hasOwn';
import {
  addErrorMessages,
  removeErrorMessages,
} from '../../../includes/streamFieldErrors';
import { CollapsiblePanel } from './CollapsiblePanel';
import { initCollapsiblePanel } from '../../../includes/panels';
import { setAttrs } from '../../../utils/attrs';
import { SettingsButton } from './ActionButton';

export class StructBlock {
  #initialState;
  #initialError;

  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;
    this.#initialState = initialState || {};
    this.#initialError = initialError;

    this.childBlocks = {};

    if (blockDef.meta.formTemplate) {
      const html = blockDef.meta.formTemplate.replace(/__PREFIX__/g, prefix);

      let dom;
      if (this.blockDef.collapsible) {
        const container = new CollapsiblePanel({
          panelId: prefix + '-section',
          headingId: prefix + '-heading',
          contentId: prefix + '-content',
          blockTypeIcon: h(blockDef.meta.icon),
          blockTypeLabel: h(blockDef.meta.label),
          collapsed: blockDef.meta.collapsed,
        }).render().outerHTML;
        // Replace the placeholder with the collapsible panel container so it's
        // mounted to the DOM and can be initialized.
        dom = $(container);
        $(placeholder).replaceWith(dom);
        // Initialize the collapsible panel and append the form template HTML
        // to the content area of the collapsible panel.
        dom = this.#initializeCollapsiblePanel(dom, prefix);
        dom.append(html);
      } else {
        // Collapsible panel is handled by the parent block, so just
        // replace the placeholder with the form template HTML.
        dom = $(html);
        $(placeholder).replaceWith(dom);
      }

      const blockErrors = initialError?.blockErrors || {};
      this.blockDef.childBlockDefs.forEach((childBlockDef) => {
        const childBlockElement = dom
          .find('[data-structblock-child="' + childBlockDef.name + '"]')
          .get(0);
        const childBlock = childBlockDef.render(
          childBlockElement,
          prefix + '-' + childBlockDef.name,
          this.#initialState[childBlockDef.name],
          blockErrors[childBlockDef.name],
        );
        this.childBlocks[childBlockDef.name] = childBlock;
      });
      this.container = dom;
    } else {
      this.container = this.renderGroup(this.blockDef, placeholder, prefix);
    }

    // Set in initialisation regardless of block state for screen reader users.
    if (this.blockDef.collapsible) {
      this.setTextLabel();
    }

    setAttrs(this.container[0], this.blockDef.meta.attrs || {});
  }

  #initializeCollapsiblePanel(dom, prefix) {
    const collapsibleToggle = dom.find('[data-panel-toggle]')[0];
    const collapsibleTitle = dom.find('[data-panel-heading-text]')[0];
    initCollapsiblePanel(collapsibleToggle);
    const setTextLabel = () => {
      const label = this.getTextLabel({ maxLength: 50 }, dom[0]);
      collapsibleTitle.textContent = label || '';
    };
    collapsibleToggle.addEventListener('wagtail:panel-toggle', setTextLabel);
    if (!this.setTextLabel) {
      this.setTextLabel = setTextLabel;
    }
    return dom.find(`#${prefix}-content`);
  }

  renderChildBlockDef(childBlockDef, container) {
    const isStructBlock =
      // Cannot use `instanceof StructBlockDefinition` here as it is defined
      // later in this file. Compare our own blockDef constructor instead.
      childBlockDef instanceof this.blockDef.constructor;

    // Struct blocks are collapsible and thus have their own header,
    // so only add the label if this is not a struct block.
    let label = '';
    if (!isStructBlock) {
      label = `<label class="w-field__label">${h(childBlockDef.meta.label)}${
        childBlockDef.meta.required
          ? '<span class="w-required-mark">*</span>'
          : ''
      }</label>`;
    }

    const childDom = $(`
        <div data-contentpath="${childBlockDef.name}">
          ${label}
            <div data-streamfield-block></div>
          </div>
        `);
    container.append(childDom);
    const childBlockElement = childDom.find('[data-streamfield-block]').get(0);
    const labelElement = childDom.find('label').get(0);
    const blockErrors = this.#initialError?.blockErrors || {};
    const childBlock = childBlockDef.render(
      childBlockElement,
      this.prefix + '-' + childBlockDef.name,
      this.#initialState[childBlockDef.name],
      blockErrors[childBlockDef.name],
      new Map(),
    );

    this.childBlocks[childBlockDef.name] = childBlock;
    if (childBlock.idForLabel) {
      labelElement.setAttribute('for', childBlock.idForLabel);
    }
  }

  renderGroup(group, container, prefix) {
    const isBlockDef = group === this.blockDef;
    const opts = isBlockDef ? this.blockDef.meta : group.opts;

    let dom = $(`
      <div class="${h(opts.classname || '')}">
      </div>
    `);

    // For the StructBlock definition itself, we need to replace the placeholder
    // element rendered by the server, otherwise we just append to the container.
    if (isBlockDef) {
      $(container).replaceWith(dom);
    } else {
      container.append(dom);
    }

    // If it's a BlockGroup, always wrap in a collapsible panel. If it's the
    // StructBlock defintion itself, we wrap in a collapsible panel only if it's
    // not already handled by the parent block.
    if (!isBlockDef || this.blockDef.collapsible) {
      const groupContainer = new CollapsiblePanel({
        panelId: `${prefix}-section`,
        headingId: `${prefix}-heading`,
        contentId: `${prefix}-content`,
        blockTypeIcon: h(opts.icon),
        blockTypeLabel: h(opts.heading),
        collapsed: dom.hasClass('collapsed'),
      }).render().outerHTML;
      dom.append(groupContainer);
      dom = this.#initializeCollapsiblePanel(dom, prefix);
    }

    if (opts.helpText) {
      // help text is left unescaped as per Django conventions
      dom.append(`
        <div class="c-sf-help">
          <div class="help">
            ${opts.helpText}
          </div>
        </div>
      `);
    }

    const { children, settings } = isBlockDef
      ? this.blockDef.meta.formLayout.opts
      : opts;

    if (settings.length > 0) {
      dom.append(/* html */ `
        <div id="${prefix}-settings" data-block-settings hidden="until-found"></div>
      `);

      const panel = dom.closest('[data-panel]');
      const controls = panel.find('[data-panel-controls]').get(0);
      const settingsButton = new SettingsButton({ element: dom.get(0) });
      settingsButton.render(controls);

      const blockSettings = dom.find('[data-block-settings]');
      settings.forEach(([entry, id]) =>
        this.#renderLayoutEntry(entry, blockSettings, `${prefix}-${id}`),
      );
    }

    children.forEach(([entry, id]) =>
      this.#renderLayoutEntry(entry, dom, `${prefix}-${id}`),
    );

    return dom;
  }

  #renderLayoutEntry(layoutEntry, container, prefix) {
    if (typeof layoutEntry === 'string') {
      // it's a block name, render the block
      const childBlockDef = this.blockDef.childBlockDefsMap[layoutEntry];
      this.renderChildBlockDef(childBlockDef, container);
      return;
    }
    // it's a BlockGroup, render with a collapsible panel
    this.renderGroup(layoutEntry, container, prefix);
  }

  setState(state) {
    // eslint-disable-next-line guard-for-in, no-restricted-syntax
    for (const name in state) {
      this.childBlocks[name].setState(state[name]);
    }
  }

  setError(error) {
    if (!error) return;

    // Non block errors
    const container = this.container[0];
    removeErrorMessages(container);
    if (error.messages) {
      addErrorMessages(container, error.messages);
    }

    if (error.blockErrors) {
      // eslint-disable-next-line no-restricted-syntax
      for (const blockName in error.blockErrors) {
        if (hasOwn(error.blockErrors, blockName)) {
          const block = this.childBlocks[blockName];
          block.setError(error.blockErrors[blockName]);

          // Trigger a 'beforematch' event on the errored block to ensure it's
          // expanded if it's within any level of collapsible panels, including
          // settings panels.
          const element = block.element || block.container?.[0];
          element.dispatchEvent(new Event('beforematch', { bubbles: true }));
        }
      }
    }
  }

  getState() {
    const state = {};
    // eslint-disable-next-line guard-for-in, no-restricted-syntax
    for (const name in this.childBlocks) {
      state[name] = this.childBlocks[name].getState();
    }
    return state;
  }

  getDuplicatedState() {
    const state = {};
    // eslint-disable-next-line guard-for-in, no-restricted-syntax
    for (const name in this.childBlocks) {
      const block = this.childBlocks[name];
      state[name] =
        block.getDuplicatedState === undefined
          ? block.getState()
          : block.getDuplicatedState();
    }
    return state;
  }

  getValue() {
    const value = {};
    // eslint-disable-next-line guard-for-in, no-restricted-syntax
    for (const name in this.childBlocks) {
      value[name] = this.childBlocks[name].getValue();
    }
    return value;
  }

  getTextLabel(opts, container = null) {
    // Allow using the empty string for the additional text in collapsed state
    if (typeof this.blockDef.meta.labelFormat === 'string') {
      /* use labelFormat - regexp replace any field references like '{first_name}'
      with the text label of that sub-block */
      return this.blockDef.meta.labelFormat.replace(
        /\{(\w+)\}/g,
        (tag, blockName) => {
          const block = this.childBlocks[blockName];
          if (block && block.getTextLabel) {
            /* to be strictly correct, we should be adjusting opts.maxLength to account for the overheads
          in the format string, and dividing the remainder across all the placeholders in the string,
          rather than just passing opts on to the child. But that would get complicated, and this is
          better than nothing... */
            return block.getTextLabel(opts);
          }
          return '';
        },
      );
    }

    /* if no labelFormat specified, just try each child block in turn until we find one that provides a label */
    for (const childDef of this.blockDef.childBlockDefs) {
      const child = this.childBlocks[childDef.name];
      if (
        container &&
        !container.contains(child.container?.[0] || child.element)
      ) {
        // eslint-disable-next-line no-continue
        continue;
      }
      if (child.getTextLabel) {
        const val = child.getTextLabel(opts);
        if (val) return val;
      }
    }
    // no usable label found
    return null;
  }

  focus(opts) {
    if (this.blockDef.childBlockDefs.length) {
      const firstChildName = this.blockDef.childBlockDefs[0].name;
      this.childBlocks[firstChildName].focus(opts);
    }
  }
}

export class BlockGroupDefinition {
  constructor(opts) {
    this.opts = opts;
  }
}

export class StructBlockDefinition {
  constructor(name, childBlockDefs, meta) {
    this.name = name;
    this.childBlockDefs = childBlockDefs;
    this.childBlockDefsMap = childBlockDefs.reduce((map, blockDef) => {
      map[blockDef.name] = blockDef;
      return map;
    }, {});
    this.meta = meta;

    // Always collapsible by default, but can be overridden e.g. when used in a
    // StreamBlock or ListBlock, in which case the collapsible behavior is
    // controlled by the parent block.
    this.collapsible = true;
  }

  render(placeholder, prefix, initialState, initialError) {
    return new StructBlock(
      this,
      placeholder,
      prefix,
      initialState,
      initialError,
    );
  }
}
