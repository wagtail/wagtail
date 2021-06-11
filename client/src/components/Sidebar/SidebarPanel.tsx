/* eslint-disable react/prop-types */

import * as React from 'react';

export interface SidebarPanelProps {
  isVisible: boolean;
  isOpen: boolean;
  depth: number;
}

export const SidebarPanel: React.FunctionComponent<SidebarPanelProps> = (
  { isVisible, isOpen, depth, children }) => {
  const className = (
    'sidebar-panel'
    + (isVisible ? ' sidebar-panel--visible' : '')
    + (isOpen ? ' sidebar-panel--open' : '')
  );

  return (
    <div className={className} style={{ zIndex: -depth }}>
      {children}
    </div>
  );
};
