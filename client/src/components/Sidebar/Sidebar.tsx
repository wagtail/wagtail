import * as React from 'react';

import Icon from '../Icon/Icon';

// Please keep in sync with $menu-transition-duration variable in `client/scss/settings/_variables.scss`
export const SIDEBAR_TRANSITION_DURATION = 150;

export interface Strings {
  DASHBOARD: string;
  EDIT_YOUR_ACCOUNT: string,
  SEARCH: string,
  TOGGLE_SIDEBAR: string,
  MAIN_MENU: string,
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
  const [collapsed, setCollapsed] = React.useState(collapsedOnLoad);

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

  // 'visibleOnMobile' indicates whether the sidebar is currently visible on mobile
  // On mobile, the sidebar is completely hidden by default and must be opened manually
  const [visibleOnMobile, setVisibleOnMobile] = React.useState(false);

  // Tracks whether the screen is below 800 pixels. In this state, the menu is completely hidden.
  // State is used here in case the user changes their browser size
  const checkWindowSizeIsMobile = () => window.innerWidth < 800;
  const [isMobile, setIsMobile] = React.useState(checkWindowSizeIsMobile());
  React.useEffect(() => {
    function handleResize() {
      if (checkWindowSizeIsMobile()) {
        setIsMobile(true);
      } else {
        setIsMobile(false);

        // Close the menu as this state is not used in desktop
        setVisibleOnMobile(false);
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

    if (onExpandCollapse) {
      onExpandCollapse(!collapsed);
    }
  };

  const onClickOpenCloseToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    setVisibleOnMobile(!visibleOnMobile);
    setExpandingOrCollapsing(true);

    const finishTimeout = setTimeout(() => {
      setExpandingOrCollapsing(false);
    }, SIDEBAR_TRANSITION_DURATION);
    return () => {
      clearTimeout(finishTimeout);
    };
  };

  // Switch peeking on/off when the mouse cursor hovers the sidebar or focus is on the sidebar
  const [mouseHover, setMouseHover] = React.useState(false);
  const [focused, setFocused] = React.useState(false);

  const onMouseEnterHandler = () => {
    setMouseHover(true);
  };

  const onMouseLeaveHandler = () => {
    setMouseHover(false);
  };

  const onFocusHandler = () => {
    setFocused(true);
  };

  const onBlurHandler = () => {
    setFocused(false);
  };

  // We need a stop peeking timeout to stop the sidebar moving as someone tab's though the menu
  const stopPeekingTimeout = React.useRef<any>(null);

  React.useEffect(() => {
    if (mouseHover || focused) {
      clearTimeout(stopPeekingTimeout.current);
      setPeeking(true);
    } else {
      clearTimeout(stopPeekingTimeout.current);
      stopPeekingTimeout.current = setTimeout(() => {
        setPeeking(false);
      }, SIDEBAR_TRANSITION_DURATION);
    }
  }, [mouseHover, focused]);

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
      <div
        className={
          'sidebar'
          + (slim ? ' sidebar--slim' : '')
          + (isMobile ? ' sidebar--mobile' : '')
          + ((isMobile && !visibleOnMobile) ? ' sidebar--hidden' : '')
        }
      >
        <div className="sidebar__inner">
          <button
            onClick={onClickCollapseToggle}
            aria-label={strings.TOGGLE_SIDEBAR}
            aria-expanded={!slim}
            className="button sidebar__collapse-toggle"
          >
            {collapsed ? <Icon name="angle-double-right" /> : <Icon name="angle-double-left" />}
          </button>

          <div
            className="sidebar__peek-hover-area"
            onMouseEnter={onMouseEnterHandler}
            onMouseLeave={onMouseLeaveHandler}
            onFocus={onFocusHandler}
            onBlur={onBlurHandler}
          >
            {renderedModules}
          </div>
        </div>
      </div>
      <button
        onClick={onClickOpenCloseToggle}
        aria-label={strings.TOGGLE_SIDEBAR}
        aria-expanded={visibleOnMobile}
        className={
          'button sidebar-nav-toggle'
          + (isMobile ? ' sidebar-nav-toggle--mobile' : '')
          + (visibleOnMobile ? ' sidebar-nav-toggle--open' : '')
        }
      >
        {visibleOnMobile ? <Icon name="cross" /> : <Icon name="bars" />}
      </button>
    </>
  );
};
