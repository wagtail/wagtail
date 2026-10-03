import type { Result } from 'axe-core';
import type { ErrorMessages } from './contentChecker';
import tippy, { type Instance, type Props } from 'tippy.js';
import { hideTooltipOnEsc } from '../controllers/TooltipController';
import { getViolationMessage } from './contentChecker';

let nextAnnotationId = 0;

/**
 * Lightweight inline annotation that displays CMS information or interactions
 * related to a specific page element.
 */
export class InlineUserbar extends HTMLElement {
  declare tippyInstance: Instance<Props>;
  declare toggle: HTMLButtonElement;
  declare targetElement: HTMLElement;
  declare resizeObserver: ResizeObserver;
  private currentScale = 1;

  connectedCallback() {
    const userbarShadow = document.querySelector('wagtail-userbar')?.shadowRoot;
    if (!userbarShadow) return;

    const wrapperTemplate = userbarShadow.querySelector<HTMLTemplateElement>(
      `#w-inline-userbar-template`,
    );
    if (!wrapperTemplate) return;

    const shadowRoot = this.attachShadow({ mode: 'open' });

    this.targetElement = document.querySelector(
      this.getAttribute('data-selector')!,
    ) as HTMLElement;

    this.copyUIAssets(userbarShadow, shadowRoot);
    shadowRoot.appendChild(wrapperTemplate.content.cloneNode(true));

    // Give each annotation landmark a label matching its toggle button.
    nextAnnotationId += 1;

    this.toggle = shadowRoot.querySelector(
      '[data-inline-userbar-toggle]',
    ) as HTMLButtonElement;
    this.toggle.id = `w-inline-userbar-toggle-${nextAnnotationId}`;
    const aside = shadowRoot.querySelector('aside') as HTMLElement;
    aside.setAttribute('aria-labelledby', this.toggle.id);

    const contentTemplate = userbarShadow.querySelector(
      `#w-inline-userbar-content-checker-template`,
    ) as HTMLTemplateElement;
    const content = shadowRoot.querySelector(
      '[data-inline-userbar-content]',
    ) as HTMLElement;
    content.appendChild(contentTemplate.content.cloneNode(true));

    const nameEl = shadowRoot.querySelector(
      '[data-content-checker-name]',
    ) as HTMLSpanElement;
    const helpEl = shadowRoot.querySelector(
      '[data-content-checker-help]',
    ) as HTMLDivElement;
    nameEl.textContent = this.getAttribute('data-error-name') || '';
    helpEl.textContent = this.getAttribute('data-help-text') || '';

    content.hidden = false;

    this.tippyInstance = tippy(this.toggle, {
      content,
      trigger: 'click',
      interactive: true,
      arrow: true,
      maxWidth: 350,
      placement: 'bottom-end',
      theme: 'dropdown',
      plugins: [hideTooltipOnEsc],
      appendTo: () => aside,
      onShow: () => this.toggleTargetOutline(true),
      onHide: () => this.toggleTargetOutline(false),
      // Tippy uses getBoundingClientRect which returns viewport-scaled
      // coordinates. When a CSS transform scales the host, the popper's
      // local coordinate space differs from the viewport. Dividing by the
      // current scale converts back to local coordinates.
      getReferenceClientRect: () => {
        const rect = this.toggle.getBoundingClientRect();
        const scale = this.currentScale;
        return {
          width: rect.width / scale,
          height: rect.height / scale,
          top: rect.top / scale,
          bottom: rect.bottom / scale,
          left: rect.left / scale,
          right: rect.right / scale,
          x: rect.x / scale,
          y: rect.y / scale,
        } as DOMRect;
      },
    });

    this.positionAtTarget();
  }

  /**
   * Clone stylesheets and icons from the main userbar to guarantee parity.
   */
  private copyUIAssets(source: ShadowRoot, target: ShadowRoot) {
    const assets = source.querySelector<HTMLElement>('[data-userbar-assets]');
    if (assets) target.appendChild(assets.cloneNode(true));
  }

  private positionAtTarget() {
    if (!this.targetElement) return;

    this.updatePosition();

    this.resizeObserver = new ResizeObserver(() => this.updatePosition());
    this.resizeObserver.observe(this.targetElement);
  }

  /**
   * Recompute the annotation's position relative to its target element.
   */
  updatePosition() {
    if (!this.targetElement) return;
    const targetRect = this.targetElement.getBoundingClientRect();

    // Compute position relative to offsetParent, since position:absolute
    // is resolved against the nearest positioned ancestor, not the viewport.
    const offsetParent = this.offsetParent as HTMLElement | null;
    const parentRect = offsetParent
      ? offsetParent.getBoundingClientRect()
      : { top: 0, left: 0 };

    this.style.setProperty(
      '--inline-userbar-top',
      `${targetRect.bottom - parentRect.top}px`,
    );
    this.style.setProperty(
      '--inline-userbar-inline-start',
      `${targetRect.right - parentRect.left}px`,
    );
  }

  /**
   * Scroll the target element into view, show the outline, and move focus
   * to the toggle button. Used by the checker results dialog's crosshair
   * button to navigate the user to the annotation.
   */
  focusTarget() {
    this.targetElement.style.scrollMargin = '6.25rem';
    this.targetElement.scrollIntoView();
    this.toggleTargetOutline(true);
    this.targetElement.focus();
  }

  /**
   * Counteract the preview iframe's CSS scaling to keep annotations legible.
   */
  setScale(scale: number) {
    this.currentScale = scale;
    this.style.setProperty('--inline-userbar-scale', String(scale));
    this.updatePosition();
    this.tippyInstance?.popperInstance?.update();
  }

  toggleTargetOutline(outline: boolean) {
    if (outline) {
      this.targetElement.style.outline = '1px solid #CD4444';
      this.targetElement.style.boxShadow = '0px 0px 12px 1px #FF0000';
    } else {
      this.targetElement.style.outline = '';
      this.targetElement.style.boxShadow = '';
    }
  }

  disconnectedCallback() {
    this.toggleTargetOutline(false);
    this.tippyInstance.destroy();
    this.resizeObserver.disconnect();
  }

  /**
   * Create annotation elements for content checker violations and insert
   * them right after each problem element so keyboard tab order follows
   * document reading order. Returns the created elements for cleanup.
   */
  static createAnnotations(
    violations: Result[],
    messages: ErrorMessages,
  ): InlineUserbar[] {
    const annotations: InlineUserbar[] = [];

    for (const violation of violations) {
      for (const node of violation.nodes) {
        const selectorParts = node.target.filter(
          (part) => part !== '#w-preview-iframe',
        );
        const selector = Array.isArray(selectorParts[0])
          ? selectorParts[0].join(' ')
          : selectorParts.join(' ');

        const targetElement = document.querySelector<HTMLElement>(selector);

        if (targetElement) {
          const { name, helpText } = getViolationMessage(violation, messages);

          const el = document.createElement(
            'wagtail-inline-userbar',
          ) as InlineUserbar;
          el.setAttribute('data-selector', selector);
          el.setAttribute('data-error-name', name);
          el.setAttribute('data-help-text', helpText);

          // Risk of conflicts with sibling / hierarchy selectors (+, ~, :nth-child, :last-child).
          targetElement.insertAdjacentElement('afterend', el);
          annotations.push(el);
        }
      }
    }

    return annotations;
  }

  /**
   * Remove all inline userbar annotations from the page.
   */
  static clearAnnotations(annotations: InlineUserbar[]) {
    for (const el of annotations) {
      el.remove();
    }
  }
}
