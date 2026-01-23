import React from 'react';

import { ngettext } from '../../utils/gettext';
import Icon from '../Icon/Icon';

export interface MinimapMenuItem {
  anchor: HTMLAnchorElement;
  toggle: HTMLButtonElement;
  panel: HTMLElement;
  href: string;
  label: string;
  icon: string;
  required: boolean;
  errorCount: number;
  level: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

interface MinimapItemProps {
  item: MinimapMenuItem;
  intersects: boolean;
  expanded: boolean;
  onClick: (item: MinimapMenuItem, e: React.MouseEvent) => void;
}

const requiredMark = <span className="w-required-mark">*</span>;

/**
 * A single menu item inside the minimap, linking to a section of the page.
 */
const MinimapItem: React.FunctionComponent<MinimapItemProps> = ({
  item,
  intersects,
  expanded,
  onClick,
}) => {
  const { href, label, icon, required, errorCount, level } = item;
  const hasError = errorCount > 0;
  const errorsLabel = ngettext(
    '%(num)s error',
    '%(num)s errors',
    errorCount,
  ).replace('%(num)s', `${errorCount}`);
  const text = label.length > 22 ? `${label.substring(0, 22)}…` : label;
  return (
    <a
      href={href}
      className={`w-minimap-item w-minimap-item--${level} ${
        intersects ? 'w-minimap-item--active' : ''
      } ${hasError ? 'w-minimap-item--error' : ''}`}
      onClick={onClick.bind(null, item)}
      aria-current={intersects}
      // Prevent interacting with the links when they are only partially shown.
      tabIndex={expanded ? undefined : -1}
      // Use the toggle button as description when collapsed.
      aria-describedby={expanded ? undefined : 'w-minimap-toggle'}
    >
      {hasError ? (
        <div className="w-minimap-item__errors" aria-label={errorsLabel}>
          {errorCount}
        </div>
      ) : null}
      <Icon name="minus" className="w-minimap-item__placeholder" />
      {level !== 'h1' && level !== 'h2' ? (
        <Icon name={icon} className="w-minimap-item__icon" />
      ) : null}
      <span className="w-minimap-item__label">
        <span className="w-minimap-item__text">{text}</span>
        {required ? requiredMark : null}
      </span>
    </a>
  );
};

export default MinimapItem;
