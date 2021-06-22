/* eslint-disable react/prop-types */

import * as React from 'react';

export interface SidebarPanelProps {
  isVisible: boolean;
  isOpen: boolean;
  depth: number;
  widthPx?: number;
}

export const SidebarPanel: React.FunctionComponent<SidebarPanelProps> = (
  { isVisible, isOpen, depth, widthPx, children }) => {
  const className = (
    'sidebar-panel'
    + (isVisible ? ' sidebar-panel--visible' : '')
    + (isOpen ? ' sidebar-panel--open' : '')
  );

  const style = { zIndex: -depth };
  if (widthPx) {
    style['--width'] = widthPx + 'px';
  }

  return (
    <div className={className} style={style}>
      {children}
    </div>
  );
};
