import { gettext } from '../../../utils/gettext';

interface PanelProps {
  panelId: string;
  headingId: string;
  contentId: string;
  blockDef?: {
    meta: {
      required?: boolean;
    };
  };
  blockTypeIcon: string;
  blockTypeLabel: string;
  collapsed?: boolean;
}

/**
 * JavaScript equivalent of the {% panel %} template tag.
 */
export class CollapsiblePanel {
  declare props: PanelProps;

  constructor(props: PanelProps) {
    this.props = props;
  }

  render() {
    const template = document.createElement('template');
    const {
      panelId,
      headingId,
      contentId,
      blockDef,
      blockTypeIcon,
      blockTypeLabel,
      collapsed,
    } = this.props;

    // Keep in sync with wagtailadmin/shared/panel.html
    template.innerHTML = /* html */ `
        <section class="w-panel w-panel--nested${collapsed ? ' collapsed' : ''}" id="${panelId}" aria-labelledby="${headingId}" data-panel>
          <div class="w-panel__header">
            <a class="w-panel__anchor w-panel__anchor--prefix" href="#${panelId}" aria-labelledby="${headingId}" data-panel-anchor>
              <svg class="icon icon-link w-panel__icon" aria-hidden="true">
                <use href="#icon-link"></use>
              </svg>
            </a>
            <button class="w-panel__toggle" type="button" aria-label="${gettext('Toggle section')}" aria-describedby="${headingId}" data-panel-toggle aria-controls="${contentId}" aria-expanded="true">
              <svg class="icon icon-${blockTypeIcon} w-panel__icon" aria-hidden="true">
                <use href="#icon-${blockTypeIcon}"></use>
              </svg>
            </button>
            <h2 class="w-panel__heading w-panel__heading--label" aria-level="3" id="${headingId}" data-panel-heading>
              <span class="c-sf-block__type">${blockTypeLabel}</span>
              ${
                blockDef?.meta.required
                  ? '<span class="w-required-mark" data-panel-required>*</span>'
                  : ''
              }
              <span data-panel-heading-text class="c-sf-block__title"></span>
            </h2>
            <a class="w-panel__anchor w-panel__anchor--suffix" href="#${panelId}" aria-labelledby="${headingId}">
              <svg class="icon icon-link w-panel__icon" aria-hidden="true">
                <use href="#icon-link"></use>
              </svg>
            </a>
            <div class="w-panel__divider"></div>
            <div class="w-panel__controls" data-panel-controls></div>
          </div>
          <div id="${contentId}" class="w-panel__content">
            ${blockDef ? '<div data-streamfield-block></div>' : ''}
          </div>
        </section>
    `;
    return template.content.firstElementChild as HTMLElement;
  }
}
