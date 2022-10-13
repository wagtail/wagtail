import React from 'react';

import { gettext } from '../../utils/gettext';
import Icon from '../Icon/Icon';

export interface MinimapMenuItem {
  anchor: HTMLAnchorElement;
  toggle: HTMLButtonElement;
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
  const { href, label, icon, required, errorCount, level } = item;
  const hasError = errorCount > 0;
  return (
    <a
      href={href}
      className={`w-minimap-item w-minimap-item--${level} ${
        intersects ? 'w-minimap-item--active' : ''
      } ${hasError ? 'w-minimap-item--error' : ''}`}
      onClick={onClick}
    >
      {hasError ? (
        <div
          className="w-minimap-item__errors"
          aria-label={gettext('{count} errors').replace(
            '{count}',
            `${errorCount}`,
          )}
        >
          {errorCount}
        </div>
      ) : null}
      <Icon name="minus" className="w-minimap-item__placeholder" />
      {level !== 'h1' && level !== 'h2' ? (
        <Icon name={icon || ' arrow-right'} className="w-minimap-item__icon" />
      ) : null}
      <span className="w-minimap-item__label">
        <span className="w-minimap-item__text">{label}</span>
        {required ? requiredMark : null}
      </span>
    </a>
  );
};

export default MinimapItem;
