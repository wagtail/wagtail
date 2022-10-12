import React from 'react';

import { gettext } from '../../utils/gettext';
import Icon from '../Icon/Icon';

export interface MinimapMenuItem {
  anchor: HTMLAnchorElement;
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
  onClick: (e: React.MouseEvent) => void;
}

const requiredMark = <span className="w-required-mark">*</span>;

/**
 * TODO;
 */
const MinimapItem: React.FunctionComponent<MinimapItemProps> = ({
  item,
  intersects,
  onClick,
}) => {
  const hasError = item.errorCount > 0;
  return (
    <a
      href={item.href}
      className={`w-minimap-item w-minimap-item--${item.level} ${
        intersects ? 'w-minimap-item--active' : ''
      } ${hasError ? 'w-minimap-item--error' : ''}`}
      onClick={onClick}
    >
      {hasError ? (
        <div
          className="w-minimap-item__errors"
          aria-label={gettext('{count} errors').replace(
            '{count}',
            `${item.errorCount}`,
          )}
        >
          {item.errorCount}
        </div>
      ) : null}
      <Icon name="minus" className="w-minimap-item__placeholder" />
      {item.icon ? (
        <Icon name={item.icon} className="w-minimap-item__icon" />
      ) : null}
      {item.label}
      {item.required ? requiredMark : null}
    </a>
  );
};

export default MinimapItem;
