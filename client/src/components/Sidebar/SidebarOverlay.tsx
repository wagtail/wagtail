/* eslint-disable react/prop-types */

import * as React from 'react';

export interface SidebarOverlayProps {
  isVisible: boolean;
  isOpen: boolean;
}

export const SidebarOverlay: React.FunctionComponent<SidebarOverlayProps> = (
  { isVisible, isOpen, children }) => {
  const className = (
    'sidebar-overlay'
    + (isVisible ? ' sidebar-overlay--visible' : '')
    + (isOpen ? ' sidebar-overlay--open' : '')
  );

  return (
    <div className={className}>
      {children}
    </div>
  );
};
