import * as React from 'react';

import Icon from '../Icon/Icon';

// Please keep in sync with $menu-transition-duration variable in `client/scss/settings/_variables.scss`
export const SIDEBAR_TRANSITION_DURATION = 150;

export interface Strings {
  DASHBOARD: string;
  EDIT_YOUR_ACCOUNT: string;
  SEARCH: string;
  TOGGLE_SIDEBAR: string;
  MAIN_MENU: string;
}

export interface ModuleRenderContext {
  key: number;
  slim: boolean;
  expandingOrCollapsing: boolean;
  onAccountExpand: () => void;
  onSearchClick: () => void;
  onSearchBlur: () => void;
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

export const Sidebar: React.FunctionComponent<SidebarProps> = ({
  modules,
  currentPath,
  collapsedOnLoad = false,
  strings,
  navigate,
  onExpandCollapse,
}) => {
  // 'collapsed' is a persistent state that is controlled by the arrow icon at the top
  // It records the user's general preference for a collapsed/uncollapsed menu
  // This is just a hint though, and we may still collapse the menu if the screen is too small
  const [collapsed, setCollapsed] = React.useState(collapsedOnLoad);

  // Call onExpandCollapse(true) if menu is initialised in collapsed state
  React.useEffect(() => {
    if (collapsed && onExpandCollapse) {
      onExpandCollapse(true);
    }
  }, []);

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
  const slim = collapsed && !isMobile;

  // 'expandingOrCollapsing' is set to true whilst the the menu is transitioning between slim and expanded layouts
  const [expandingOrCollapsing, setExpandingOrCollapsing] =
    React.useState(false);
  React.useEffect(() => {
    setExpandingOrCollapsing(true);
    const finishTimeout = setTimeout(() => {
      setExpandingOrCollapsing(false);
    }, SIDEBAR_TRANSITION_DURATION);

    return () => {
      clearTimeout(finishTimeout);
    };
  }, [slim]);

  const onClickCollapseToggle = () => {
    setCollapsed(!collapsed);

    if (onExpandCollapse) {
      onExpandCollapse(!collapsed);
    }
  };

  const onClickOpenCloseToggle = () => {
    setVisibleOnMobile(!visibleOnMobile);
    setExpandingOrCollapsing(true);

    const finishTimeout = setTimeout(() => {
      setExpandingOrCollapsing(false);
    }, SIDEBAR_TRANSITION_DURATION);
    return () => {
      clearTimeout(finishTimeout);
    };
  };

  const [focused, setFocused] = React.useState(false);

  const onBlurHandler = () => {
    if (focused) {
      setFocused(false);
      setCollapsed(true);
    }
  };

  const onFocusHandler = () => {
    if (focused) {
      setCollapsed(false);
      setFocused(true);
    }
  };

  const onSearchClick = () => {
    if (slim) {
      onClickCollapseToggle();
    }
  };

  const onSearchBlur = () => {
    setCollapsed(true);
    setFocused(false);
  };

  const onAccountExpand = () => {
    if (slim) {
      onClickCollapseToggle();
    }
  };

  // Render modules
  const renderedModules = modules.map((module, index) =>
    module.render({
      key: index,
      slim,
      expandingOrCollapsing,
      onAccountExpand,
      onSearchClick,
      onSearchBlur,
      currentPath,
      strings,
      navigate,
    }),
  );

  return (
    <>
      <div
        className={
          'sidebar' +
          (slim ? ' sidebar--slim' : '') +
          (isMobile ? ' sidebar--mobile' : '') +
          (isMobile && !visibleOnMobile ? ' sidebar--hidden' : '')
        }
      >
        <div className="sidebar__inner">
          <button
            onClick={onClickCollapseToggle}
            aria-label={strings.TOGGLE_SIDEBAR}
            aria-expanded={slim ? 'false' : 'true'}
            type="button"
            className="button sidebar__collapse-toggle hover:w-bg-primary-200 hover:text-white hover:opacity-100"
          >
            <Icon
              name="expand-right"
              className={`w-transition motion-reduce:w-transition-none
                ${!collapsed ? '-w-rotate-180' : ''}
                `}
            />
          </button>

          <div
            className="sidebar__peek-hover-area"
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
        aria-expanded={visibleOnMobile ? 'true' : 'false'}
        className={
          'button sidebar-nav-toggle' +
          (isMobile ? ' sidebar-nav-toggle--mobile' : '') +
          (visibleOnMobile ? ' sidebar-nav-toggle--open' : '')
        }
        type="button"
      >
        {visibleOnMobile ? <Icon name="cross" /> : <Icon name="bars" />}
      </button>
    </>
  );
};
