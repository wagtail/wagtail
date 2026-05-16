import { Controller } from '@hotwired/stimulus';

declare global {
  interface Window {
    wagtail: any;
  }
}

const EDIT_HANDLER_DATA_ID = 'w-edit-handler-data';

/**
 * Renders an interpolated summary of a panel's field values into its
 * collapsed heading, based on a format string such as
 * `"{first_name} {last_name}"`.
 *
 * Bound widgets are resolved from one of two sources:
 *  - When `widgetsIdValue` is set, the widgets are read from a telepath-packed
 *    `<script type="application/json">` element by that id. This is used by
 *    `InlinePanel` rows, where each row reuses the formset's empty-form widgets.
 *  - Otherwise, they are resolved from the page-wide edit handler exposed at
 *    `window.wagtail.editHandler`, lazily unpacked from the
 *    `#w-edit-handler-data` script element on first access.
 *
 * @example
 * ```html
 * <section
 *   data-controller="w-panel-label"
 *   data-w-panel-label-format-value="{first_name} {last_name}"
 * >
 *   <h2>
 *     <button data-panel-toggle></button>
 *     <span data-panel-heading-text>Name</span>
 *   </h2>
 * </section>
 * ```
 */
export class PanelLabelController extends Controller<HTMLElement> {
  static values = {
    fieldPrefix: { default: '', type: String },
    format: { default: '', type: String },
    widgetsId: { default: '', type: String },
  };

  /** Prefix prepended to packed-widget field names (e.g. `authors-0`). */
  declare readonly fieldPrefixValue: string;
  /** Format string with `{field_name}` placeholders to interpolate. */
  declare readonly formatValue: string;
  /** Id of a telepath-packed widgets script element; if blank, the page-wide edit handler is used instead. */
  declare readonly widgetsIdValue: string;

  /** The element receiving the interpolated summary text. */
  summary?: HTMLElement;
  /** Cached unpacked widget map for the `widgetsIdValue` source. */
  widgets?: Record<string, any> | null;

  /**
   * Moves the existing heading text into a sibling span so the original
   * element can be repurposed as a live summary, then renders the initial
   * summary text and listens for collapse/expand events to re-render.
   */
  connect() {
    const heading = this.element.querySelector<HTMLElement>(
      '[data-panel-heading-text]',
    );
    if (!heading) return;

    const staticHeading = document.createElement('span');
    while (heading.firstChild) staticHeading.appendChild(heading.firstChild);
    heading.parentNode?.insertBefore(staticHeading, heading);
    heading.classList.add('w-panel__heading-summary');
    this.summary = heading;

    this.element
      .querySelector('[data-panel-toggle]')
      ?.addEventListener('wagtail:panel-toggle', this.render);

    this.render();
  }

  disconnect() {
    this.element
      .querySelector('[data-panel-toggle]')
      ?.removeEventListener('wagtail:panel-toggle', this.render);
  }

  /**
   * Interpolates the format string with each referenced field's text label
   * and writes the result into the summary element.
   */
  render = () => {
    if (!this.summary) return;
    this.summary.textContent = this.formatValue.replace(
      /\{(\w+)\}/g,
      (_, name) =>
        this.getBoundWidget(name)?.getTextLabel?.({ maxLength: 50 }) || '',
    );
  };

  /**
   * Resolves a bound widget for the given field name, from the configured
   * source (packed widgets or the page-wide edit handler).
   */
  getBoundWidget(name: string) {
    if (this.widgetsIdValue) {
      const widget = this.getPackedWidgets()?.[name];
      if (!widget?.getByName) return null;
      const fullName = this.fieldPrefixValue
        ? `${this.fieldPrefixValue}-${name}`
        : name;
      return widget.getByName(fullName, this.element);
    }
    return (
      this.getEditHandler()?.getPanelByName?.(name)?.getBoundWidget?.() ?? null
    );
  }

  /**
   * Lazily unpacks the telepath-packed widgets script referenced by
   * `widgetsIdValue`, caching the result on this controller instance.
   */
  getPackedWidgets() {
    if (this.widgets !== undefined) return this.widgets;
    const element = document.getElementById(this.widgetsIdValue);
    if (!element || !window.telepath) {
      this.widgets = null;
      return null;
    }
    try {
      this.widgets = window.telepath.unpack(
        JSON.parse(element.textContent || ''),
      );
    } catch (error) {
      this.widgets = null;
    }
    return this.widgets;
  }

  /**
   * Returns the page-wide edit handler, unpacking it from
   * `#w-edit-handler-data` on first access if it has not already been
   * initialised. The result is cached on `window.wagtail.editHandler` so
   * subsequent callers (including `wagtailadmin.js`) reuse the same instance.
   */
  getEditHandler() {
    const wagtail = window.wagtail ?? (window.wagtail = {});
    if (wagtail.editHandler) return wagtail.editHandler;

    const element = document.getElementById(EDIT_HANDLER_DATA_ID);
    if (!element || !window.telepath) return null;

    try {
      wagtail.editHandler = window.telepath.unpack(
        JSON.parse(element.textContent || ''),
      );
    } catch (error) {
      return null;
    }
    return wagtail.editHandler;
  }
}
