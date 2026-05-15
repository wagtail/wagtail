import { Controller } from '@hotwired/stimulus';

const resolveEditHandler = (): Promise<any> => {
  const read = () => (window as any).wagtail?.editHandler ?? null;
  if (read()) return Promise.resolve(read());
  return new Promise((resolve) => {
    const afterReady = () => requestAnimationFrame(() => resolve(read()));
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', afterReady, { once: true });
    } else {
      afterReady();
    }
  });
};

export class PanelLabelController extends Controller<HTMLElement> {
  static values = {
    format: { default: '', type: String },
    widgetsId: { default: '', type: String },
    fieldPrefix: { default: '', type: String },
  };

  declare formatValue: string;
  declare widgetsIdValue: string;
  declare fieldPrefixValue: string;

  summary: HTMLElement | null = null;
  editHandler: any = null;
  cachedWidgets: any = undefined;

  getWidgets() {
    if (this.cachedWidgets !== undefined) return this.cachedWidgets;
    const element = this.widgetsIdValue
      ? document.getElementById(this.widgetsIdValue)
      : null;
    if (!element || !(window as any).telepath) {
      this.cachedWidgets = null;
      return null;
    }
    try {
      this.cachedWidgets = (window as any).telepath.unpack(
        JSON.parse(element.textContent || ''),
      );
    } catch (error) {
      this.cachedWidgets = null;
    }
    return this.cachedWidgets;
  }

  getFieldLabel(name: string): string {
    if (this.widgetsIdValue) {
      const widget = this.getWidgets()?.[name];
      if (widget && widget.getByName) {
        const fullName = this.fieldPrefixValue
          ? `${this.fieldPrefixValue}-${name}`
          : name;
        return (
          widget.getByName(fullName, this.element).getTextLabel({
            maxLength: 50,
          }) || ''
        );
      }
      return '';
    }
    const panel = this.editHandler?.getPanelByName?.(name);
    const widget = panel?.getBoundWidget?.();
    if (widget && widget.getTextLabel) {
      return widget.getTextLabel({ maxLength: 50 }) || '';
    }
    return '';
  }

  setCollapsedLabelText = () => {
    if (!this.summary) return;
    this.summary.textContent = this.formatValue.replace(
      /\{(\w+)\}/g,
      (_, name) => this.getFieldLabel(name),
    );
  };

  async connect() {
    const headingText = this.element.querySelector<HTMLElement>(
      '[data-panel-heading-text]',
    );
    if (!headingText) return;

    const staticHeading = document.createElement('span');
    while (headingText.firstChild) {
      staticHeading.appendChild(headingText.firstChild);
    }
    headingText.parentNode?.insertBefore(staticHeading, headingText);
    headingText.classList.add('w-panel__heading-summary');
    this.summary = headingText;

    const toggle = this.element.querySelector('[data-panel-toggle]');
    toggle?.addEventListener(
      'wagtail:panel-toggle',
      this.setCollapsedLabelText,
    );

    if (!this.widgetsIdValue) {
      this.editHandler = await resolveEditHandler();
    }
    this.setCollapsedLabelText();
  }

  disconnect() {
    const toggle = this.element.querySelector('[data-panel-toggle]');
    toggle?.removeEventListener(
      'wagtail:panel-toggle',
      this.setCollapsedLabelText,
    );
  }
}
