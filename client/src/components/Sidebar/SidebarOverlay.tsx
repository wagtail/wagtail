/* eslint-disable react/prop-types */

import * as React from 'react';
import FocusTrap from 'focus-trap-react';

import Button from '../Button/Button';


export interface SidebarOverlayProps {
  isVisible: boolean;
  isOpen: boolean;
  onClose();
}

export const SidebarOverlay: React.FunctionComponent<SidebarOverlayProps> = (
  { isVisible, isOpen, onClose, children }) => {
  const className = (
    'sidebar-overlay'
    + (isVisible ? ' sidebar-overlay--visible' : '')
    + (isOpen ? ' sidebar-overlay--open' : '')
  );

  return (
    <FocusTrap
      paused={!isOpen}
      focusTrapOptions={{
        onDeactivate: onClose,
        fallbackFocus: '.sidebar-overlay__close-button'
      }}
    >
      <div role="dialog" className={className}>
        <Button onClick={onClose} className="sidebar-overlay__close-button">
          Close
        </Button>
        {children}
      </div>
    </FocusTrap>
  );
};
