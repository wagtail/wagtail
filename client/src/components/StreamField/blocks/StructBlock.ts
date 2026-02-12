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
import { SettingsButton } from './ActionButtons';

/**
 * Common options for both `StructBlock.Meta` and `BlockGroup`.
 */
export interface BaseGroupOpts {
  icon: string;
  classname: string;
  attrs: Record<string, string>;
  helpText?: string;
  labelFormat?: string;
}

/**
 * A rendered group of blocks within a `StructBlock`, typically within a
 * collapsible panel.
 */
export class BlockGroup {
  /** The StructBlock's Meta class for the root BlockGroup, otherwise the BlockGroup's properties. */
  declare readonly opts: StructBlockDefinitionMeta | BlockGroupDefinitionOpts;
  /** The main content part within the group's collapsible panel. */
  declare container: JQuery;
  /** The group's collapsible panel toggle. */
  declare toggle?: HTMLButtonElement;
  /** Element that holds the extra text when the panel is collapsed. */
  declare collapsedLabel?: HTMLElement;
  /** The rendered children blocks, which may contain block or BlockGroup instances. */
  declare children: Array<BlockGroup | any>;
  /** The rendered settings blocks, which may contain block or BlockGroup instances. */
  declare settings: Array<BlockGroup | any>;
  /** The settings button instance for toggling the visibility of the settings blocks. */
  declare settingsButton?: SettingsButton;

  constructor(
    public structBlock: StructBlock,
    public groupDef: BlockGroupDefinition,
    container: JQuery,
    prefix: string,
  ) {
    this.setCollapsedLabelText = this.setCollapsedLabelText.bind(this);

    // For the root BlockGroup, options like label, icon, etc. come from the
    // StructBlock's Meta class. For nested BlockGroup, we use its own opts.
    this.opts =
      this.groupDef === this.structBlock.blockDef.meta.formLayout
        ? this.structBlock.blockDef.meta
        : this.groupDef.opts;

    this.container = this.render(container, prefix);
    this.setCollapsedLabelText();
  }

  initializeCollapsiblePanel(dom: JQuery, prefix: string) {
    this.toggle = dom.find<HTMLButtonElement>('[data-panel-toggle]')[0];
    this.collapsedLabel = dom.find('[data-panel-heading-text]')[0];
    initCollapsiblePanel(this.toggle!);
    this.toggle!.addEventListener(
      'wagtail:panel-toggle',
      this.setCollapsedLabelText,
    );
    return dom.find(`#block_group-${prefix}-content`);
  }

  render(container: JQuery, prefix: string) {
    const { opts } = this;
    const isRoot = 'formLayout' in opts;
    const hasCustomTemplate = isRoot && !!opts.formTemplate;

    let dom: JQuery;
    if (hasCustomTemplate) {
      dom = $(opts.formTemplate!.replace(/__PREFIX__/g, prefix));
    } else {
      dom = $(/* html */ `
        <div class="${h(opts.classname || '')}">
        </div>
      `);
    }

    // If it's a nested BlockGroup, always wrap in a collapsible panel. If it's
    // the root BlockGroup, we wrap in a collapsible panel only if it's not
    // already handled by the parent block.
    let groupContainer: JQuery | null = null;
    if (!isRoot || this.structBlock.blockDef.collapsible) {
      const panel = new CollapsiblePanel({
        panelId: `block_group-${prefix}-section`,
        headingId: `block_group-${prefix}-heading`,
        contentId: `block_group-${prefix}-content`,
        blockTypeIcon: h(opts.icon),
        blockTypeLabel: h(isRoot ? opts.label : opts.heading),
        collapsed: isRoot ? opts.collapsed : dom.hasClass('collapsed'),
      }).render().outerHTML;
      groupContainer = $(panel);
    }

    // For the root BlockGroup, we need to replace the placeholder element
    // rendered by the server, otherwise we just append to the container.
    if (isRoot) {
      $(container).replaceWith(groupContainer ?? dom);
    } else {
      container.append(groupContainer!);
    }

    if (groupContainer) {
      const content = this.initializeCollapsiblePanel(groupContainer, prefix);
      content.append(dom);
    }

    if (!hasCustomTemplate && opts.helpText) {
      // help text is left unescaped as per Django conventions
      dom.append(/* html */ `
        <div class="c-sf-help">
          <div class="help">
            ${opts.helpText}
          </div>
        </div>
      `);
    }

    // Children and settings are always defined in the BlockGroup, and never in
    // the StructBlock's Meta, so we use `this.groupDef.opts` instead of `this.opts`.
    const { children, settings } = this.groupDef.opts;

    this.settings = [];
    if (settings.length > 0) {
      let blockSettings: JQuery;

      const hidden = 'onbeforematch' in document.body ? 'until-found' : '';
      if (hasCustomTemplate) {
        blockSettings = dom.find('[data-block-settings]');
        blockSettings.attr('id', `block_group-${prefix}-settings`);
        blockSettings.attr('hidden', hidden);
      } else {
        blockSettings = $(/* html */ `
          <div id="block_group-${prefix}-settings" data-block-settings hidden="${hidden}">
          </div>
        `);
        dom.append(blockSettings);
      }

      const panel = dom.closest('[data-panel]');
      const controls = panel.find('[data-panel-controls]').get(0);
      this.settingsButton = new SettingsButton(blockSettings.get(0)!);
      this.settingsButton.render(controls);

      this.settings = settings.map(([entry, id]) =>
        this.renderChild(
          entry,
          blockSettings,
          `block_group-${prefix}-${id}`,
          hasCustomTemplate,
        ),
      );
    }

    this.children = children.map(([entry, id]) =>
      this.renderChild(
        entry,
        dom,
        `block_group-${prefix}-${id}`,
        hasCustomTemplate,
      ),
    );

    setAttrs(dom[0], opts.attrs || {});

    return dom;
  }

  getTextLabel(opts?: { maxLength?: number }) {
    const { labelFormat } = this.opts;

    // Allow using the empty string for the additional text in collapsed state
    if (typeof labelFormat === 'string') {
      /* use labelFormat - regexp replace any field references like '{first_name}'
      with the text label of that sub-block */
      return labelFormat.replace(/\{(\w+)\}/g, (_, blockName) => {
        const block = this.structBlock.childBlocks[blockName];
        if (block && block.getTextLabel) {
          /* to be strictly correct, we should be adjusting opts.maxLength to account for the overheads
          in the format string, and dividing the remainder across all the placeholders in the string,
          rather than just passing opts on to the child. But that would get complicated, and this is
          better than nothing... */
          return block.getTextLabel(opts);
        }
        return '';
      });
    }

    /* if no labelFormat specified, just try each child block in turn until we find one that provides a label */
    for (const child of this.children.concat(this.settings)) {
      if (
        child.getTextLabel &&
        // Only use labels from child blocks within the current container.
        // Structural blocks have a `container` property (JQuery object),
        // while field blocks have an `element` property (DOM element).
        this.container[0].contains(child.container?.[0] || child.element)
      ) {
        const val = child.getTextLabel(opts);
        if (val) return val;
      }
    }
    // no usable label found
    return null;
  }

  setCollapsedLabelText() {
    // The collapsible panel is handled by the parent block.
    if (!this.collapsedLabel) return;

    const label = this.getTextLabel({ maxLength: 50 });
    this.collapsedLabel.textContent = label || '';
  }

  renderChild(
    child: string | BlockGroupDefinition,
    container: JQuery,
    prefix: string,
    hasCustomTemplate = false,
  ) {
    if (typeof child === 'string') {
      // it's a block name, delegate the rendering to the StructBlock
      return this.structBlock.renderChildBlockDef(
        child,
        container,
        hasCustomTemplate,
        // We don't pass prefix here because the StructBlock will render the
        // child block using its own prefix and the block name. As far as form
        // elements are concerned (e.g. for `name` attributes), BlockGroups are
        // invisible, and child blocks are flatly rendered inside the StructBlock.
      );
    }
    // it's a BlockGroupDefinition, render with a collapsible panel, with
    // additional prefix to ensure unique IDs for collapsible panel furniture of
    // adjacent BlockGroups that have the same headings.
    return new BlockGroup(this.structBlock, child, container, prefix);
  }
}

/** Properties of `BlockGroup`. */
export interface BlockGroupDefinitionOpts extends BaseGroupOpts {
  readonly children: Array<[entry: string | BlockGroupDefinition, id: string]>;
  readonly settings: Array<[entry: string | BlockGroupDefinition, id: string]>;
  readonly heading: string;
  readonly cleanName: string;
}

/** An unpacked `BlockGroup` definition from Telepath. */
export class BlockGroupDefinition {
  constructor(public readonly opts: BlockGroupDefinitionOpts) {
    this.opts = opts;
  }
}

export class StructBlock {
  declare blockDef: StructBlockDefinition;
  declare type: string;
  declare prefix: string;
  declare layout: BlockGroup;
  declare container: JQuery;
  declare childBlocks: Record<string, any>;

  #initialState: Record<string, any>;
  #initialError: Record<string, any>;

  constructor(
    blockDef: StructBlockDefinition,
    placeholder: JQuery,
    prefix: string,
    initialState,
    initialError,
  ) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.prefix = prefix;
    this.#initialState = initialState || {};
    this.#initialError = initialError;

    this.childBlocks = {};
    this.layout = new BlockGroup(
      this,
      blockDef.meta.formLayout,
      placeholder,
      prefix,
    );
    this.container = this.layout.container;
  }

  renderChildBlockDef(
    name: string,
    container: JQuery,
    hasCustomTemplate = false,
  ) {
    const childBlockDef = this.blockDef.childBlockDefsByName[name];
    const blockErrors = this.#initialError?.blockErrors || {};

    if (hasCustomTemplate) {
      const childBlockElement = container
        .find('[data-structblock-child="' + childBlockDef.name + '"]')
        .get(0);
      const childBlock = childBlockDef.render(
        childBlockElement,
        this.prefix + '-' + childBlockDef.name,
        this.#initialState[childBlockDef.name],
        blockErrors[childBlockDef.name],
      );
      this.childBlocks[childBlockDef.name] = childBlock;
      return childBlock;
    }

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

    const childDom = $(/* html */ `
      <div data-contentpath="${childBlockDef.name}">
        ${label}
        <div data-streamfield-block></div>
      </div>
    `);
    container.append(childDom);
    const childBlockElement = childDom.find('[data-streamfield-block]').get(0);
    const labelElement = childDom.find('label').get(0);
    const childBlock = childBlockDef.render(
      childBlockElement,
      this.prefix + '-' + childBlockDef.name,
      this.#initialState[childBlockDef.name],
      blockErrors[childBlockDef.name],
      new Map(),
    );

    this.childBlocks[childBlockDef.name] = childBlock;
    if (childBlock.idForLabel) {
      labelElement!.setAttribute('for', childBlock.idForLabel);
    }

    return childBlock;
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

          // Structural blocks have a `container` property (JQuery object),
          // while field blocks have an `element` property (DOM element).
          const element = block.container?.[0] || block.element;

          // Trigger a 'beforematch' event on the errored block to ensure it's
          // expanded if it's within any level of collapsible panels, including
          // settings panels.
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

  getTextLabel(opts) {
    return this.layout.getTextLabel(opts);
  }

  focus(opts) {
    if (this.blockDef.childBlockDefs.length) {
      const firstChildName = this.blockDef.childBlockDefs[0].name;
      this.childBlocks[firstChildName].focus(opts);
    }
  }
}

export interface StructBlockDefinitionMeta extends BaseGroupOpts {
  required: boolean;
  label: string;
  description: string;
  blockDefId: string;
  isPreviewable: boolean;
  collapsed: boolean;
  formLayout: BlockGroupDefinition;
  formTemplate?: string;
}

export class StructBlockDefinition {
  declare name: string;
  declare childBlockDefs: any[];
  declare meta: StructBlockDefinitionMeta;
  declare childBlockDefsByName: Record<string, any>;
  declare collapsible: boolean;

  constructor(
    name: string,
    childBlockDefs: any[],
    meta: StructBlockDefinitionMeta,
  ) {
    this.name = name;
    this.childBlockDefs = childBlockDefs;
    this.childBlockDefsByName = childBlockDefs.reduce((map, blockDef) => {
      map[blockDef.name] = blockDef;
      return map;
    }, {});
    this.meta = meta;

    // Always collapsible by default, but can be overridden e.g. when used in a
    // StreamBlock or ListBlock, in which case the collapsible behavior is
    // controlled by the parent block.
    this.collapsible = true;
  }

  render(
    placeholder: JQuery,
    prefix: string,
    initialState: Record<string, any>,
    initialError: Record<string, any>,
  ) {
    return new StructBlock(
      this,
      placeholder,
      prefix,
      initialState,
      initialError,
    );
  }
}
