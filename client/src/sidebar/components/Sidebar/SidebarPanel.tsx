import * as React from 'react';

export interface SidebarPanelProps {
  isVisible: boolean;
  isOpen: boolean;
  depth: number;
  widthPx?: number;
}

export const SidebarPanel: React.FunctionComponent<SidebarPanelProps> = ({
  isVisible,
  isOpen,
  depth,
  widthPx,
  children,
}) => {
  const className =
    'sidebar-panel' +
    (isVisible ? ' sidebar-panel--visible' : '') +
    (isOpen ? ' sidebar-panel--open' : '');

  let zIndex = -depth * 2;

  const isClosing = isVisible && !isOpen;
  if (isClosing) {
    // When closing, make sure this panel displays behind any new panel that is opening
    zIndex--;
  }

  const style = {
    // See https://github.com/frenic/csstype#what-should-i-do-when-i-get-type-errors.
    ['--z-index' as any]: zIndex,
  };

  if (widthPx) {
    style['--width'] = widthPx + 'px';
  }

  return (
    <div className={className} style={style}>
      {children}
    </div>
  );
};
