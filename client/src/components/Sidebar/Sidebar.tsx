/* eslint-disable react/prop-types */

import * as React from 'react';

import Icon from '../Icon/Icon';

// Please keep in sync with $menu-transition-duration variable in `client/scss/settings/_variables.scss`
export const SIDEBAR_TRANSITION_DURATION = 150;

export interface Strings {
  DASHBOARD: string;
  EDIT_YOUR_ACCOUNT: string,
  SEARCH: string,
}

export interface ModuleRenderContext {
  key: number;
  slim: boolean;
  expandingOrCollapsing: boolean;
  currentPath: string;
  strings: Strings;
  navigate(url: string): Promise<void>;
}

export interface ModuleDefinition {
  render(context: ModuleRenderContext): React.ReactFragment;
}

export interface SidebarProps {
  modules: ModuleDefinition[];
  currentPath: string;
  strings: Strings;
  collapsedOnLoad: boolean;
  navigate(url: string): Promise<void>;
  onExpandCollapse?(collapsed: boolean);
}

export const Sidebar: React.FunctionComponent<SidebarProps> = (
  { modules, currentPath, collapsedOnLoad, strings, navigate, onExpandCollapse }) => {
  // 'collapsed' is a persistent state that is controlled by the arrow icon at the top
  // It records the user's general preference for a collapsed/uncollapsed menu
  // This is just a hint though, and we may still collapse the menu if the screen is too small
  // Also, we may display the full menu temporarily in collapsed mode (see 'peeking' below)
  const [collapsed, setCollapsed] = React.useState((): boolean => {
    if (window.innerWidth < 800 || collapsedOnLoad) {
      return true;
    }
    return false;
  });

  // 'open' indicates whether the sidebar is visible or not.
  // this is meant to be used to show/hide the menu on small screens.
  // it only has effect on small screens.
  // const [open, setOpen] = React.useState(false);
  const [open, setOpen] = React.useState(true);  // FIXME: don't mount with the sidebar open

  // Call onExpandCollapse(true) if menu is initialised in collapsed state
  React.useEffect(() => {
    if (collapsed && onExpandCollapse) {
      onExpandCollapse(true);
    }
  }, []);

  // 'peeking' is a temporary state to allow the user to peek in the menu while it is collapsed, or hidden.
  // When peeking is true, the menu renders as if it's not collapsed, but as an overlay instead of occupying
  // space next to the content
  const [peeking, setPeeking] = React.useState(false);

  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    function handleResize() {
      if (window.innerWidth < 800) {
        setIsMobile(true);
      } else {
        setIsMobile(false);
      }
    }
    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Whether or not to display the menu with slim layout.
  // Separate from 'collapsed' as the menu can still be displayed with an expanded
  // layout while in 'collapsed' mode if the user is 'peeking' into it (see above)
  const slim = collapsed && !peeking && !isMobile;

  // 'expandingOrCollapsing' is set to true whilst the the menu is transitioning between slim and expanded layouts
  const [expandingOrCollapsing, setExpandingOrCollapsing] = React.useState(false);
  React.useEffect(() => {
    setExpandingOrCollapsing(true);
    const finishTimeout = setTimeout(() => {
      setExpandingOrCollapsing(false);
    }, SIDEBAR_TRANSITION_DURATION);

    return () => {
      clearTimeout(finishTimeout);
    };
  }, [slim]);

  const onClickCollapseToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    setCollapsed(!collapsed);

    // Unpeek if the user has just collapsed the menu
    // Otherwise the menu would just stay open until the mouse leaves
    if (!collapsed) {
      setPeeking(false);
    }

    if (onExpandCollapse) {
      onExpandCollapse(!collapsed);
    }
  };

  const onClickOpenCloseToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    setOpen(!open);
    setExpandingOrCollapsing(true);

    const mainContentEl = document.getElementById('main');

    if (mainContentEl) {
      if (!open) {
        mainContentEl.classList.add('sidebar--open');
      } else {
        mainContentEl.classList.remove('sidebar--open');
      }
    }
    const finishTimeout = setTimeout(() => {
      setExpandingOrCollapsing(false);
    }, SIDEBAR_TRANSITION_DURATION);
    return () => {
      clearTimeout(finishTimeout);
    };
  };

  // Switch peeking on/off when the mouse cursor hovers the sidebar
  const startPeekingTimeout = React.useRef<any>(null);
  const stopPeekingTimeout = React.useRef<any>(null);

  const onMouseEnterHandler = () => {
    clearTimeout(startPeekingTimeout.current);
    clearTimeout(stopPeekingTimeout.current);
    startPeekingTimeout.current = setTimeout(() => {
      if (isMobile) {
        return;
      }
      setPeeking(true);
    }, 100);
  };

  const onMouseLeaveHandler = () => {
    clearTimeout(startPeekingTimeout.current);
    clearTimeout(stopPeekingTimeout.current);
    stopPeekingTimeout.current = setTimeout(() => {
      if (isMobile) {
        return;
      }
      setPeeking(false);
    }, SIDEBAR_TRANSITION_DURATION);
  };

  // Render modules
  const renderedModules = modules.map(
    (module, index) => module.render({
      key: index,
      slim,
      expandingOrCollapsing,
      currentPath,
      strings,
      navigate
    })
  );

  return (
    <>
      <aside
        className={
          'sidebar'
           + (slim ? ' sidebar--slim' : '')
           + (open ? ' sidebar--open' : '')
        }
        onMouseEnter={onMouseEnterHandler} onMouseLeave={onMouseLeaveHandler}
      >
        <div className="sidebar__inner">
          <button onClick={onClickCollapseToggle} className="button sidebar__collapse-toggle">
            {collapsed ? <Icon name="angle-double-right" /> : <Icon name="angle-double-left" />}
          </button>
          {renderedModules}
        </div>
      </aside>
      <button onClick={onClickOpenCloseToggle} className="button sidebar__nav-toggle">
        {open ? <Icon name="cross" /> : <Icon name="bars" />}
      </button>
    </>
  );
};
