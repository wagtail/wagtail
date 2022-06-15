import * as React from 'react';

import { gettext } from '../../utils/gettext';
import Icon from '../Icon/Icon';

// Please keep in sync with $menu-transition-duration variable in `client/scss/settings/_variables.scss`
export const SIDEBAR_TRANSITION_DURATION = 150;

export interface ModuleRenderContext {
  key: number;
  slim: boolean;
  expandingOrCollapsing: boolean;
  onHideMobile: () => void;
  onSearchClick: () => void;
  currentPath: string;
  navigate(url: string): Promise<void>;
}

export interface ModuleDefinition {
  render(context: ModuleRenderContext): React.ReactFragment;
}

export interface SidebarProps {
  modules: ModuleDefinition[];
  currentPath: string;
  collapsedOnLoad: boolean;
  navigate(url: string): Promise<void>;
  onExpandCollapse?(collapsed: boolean);
}

export const Sidebar: React.FunctionComponent<SidebarProps> = ({
  modules,
  currentPath,
  collapsedOnLoad = false,
  navigate,
  onExpandCollapse,
}) => {
  // 'collapsed' is a persistent state that is controlled by the arrow icon at the top
  // It records the user's general preference for a collapsed/uncollapsed menu
  // This is just a hint though, and we may still collapse the menu if the screen is too small
  const [collapsed, setCollapsed] = React.useState(collapsedOnLoad);
  const mobileNavToggleRef = React.useRef<HTMLButtonElement>(null);

  // Call onExpandCollapse(true) if menu is initialised in collapsed state
  React.useEffect(() => {
    if (collapsed && onExpandCollapse) {
      onExpandCollapse(true);
    }
  }, []);

  // 'visibleOnMobile' indicates whether the sidebar is currently visible on mobile
  // On mobile, the sidebar is completely hidden by default and must be opened manually
  const [visibleOnMobile, setVisibleOnMobile] = React.useState(false);
  // 'closedOnMobile' is used to set the menu to display none so it can no longer be interacted with by keyboard when its hidden
  const [closedOnMobile, setClosedOnMobile] = React.useState(true);

  // Tracks whether the screen is below 800 pixels. In this state, the menu is completely hidden.
  // State is used here in case the user changes their browser size
  const checkWindowSizeIsMobile = () => window.innerWidth < 800;
  const [isMobile, setIsMobile] = React.useState(checkWindowSizeIsMobile());
  React.useEffect(() => {
    function handleResize() {
      if (checkWindowSizeIsMobile()) {
        setIsMobile(true);
        return null;
      } else {
        setIsMobile(false);

        // Close the menu and animate out as this state is not used in desktop
        setVisibleOnMobile(false);
        // wait for animation to finish then hide menu from screen readers as well.
        return setTimeout(() => {
          setClosedOnMobile(true);
        }, SIDEBAR_TRANSITION_DURATION);
      }
    }

    window.addEventListener('resize', handleResize);
    const closeTimeout = handleResize();
    return () => {
      window.removeEventListener('resize', handleResize);
      if (closeTimeout) {
        clearTimeout(closeTimeout);
      }
    };
  }, []);

  // Whether or not to display the menu with slim layout.
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
      setClosedOnMobile(!closedOnMobile);
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

  React.useEffect(() => {
    // wait for animation to finish then hide menu from screen readers as well.
    const finishHidingMenu = setTimeout(() => {
      if (!visibleOnMobile) {
        setClosedOnMobile(true);
      }
    }, SIDEBAR_TRANSITION_DURATION);

    return () => {
      clearTimeout(finishHidingMenu);
    };
  }, [visibleOnMobile]);

  const onHideMobile = () => {
    setVisibleOnMobile(false);

    if (mobileNavToggleRef) {
      // When menu is closed with escape key bring focus back to open close toggle
      mobileNavToggleRef.current?.focus();
    }
  };

  // Render modules
  const renderedModules = modules.map((module, index) =>
    module.render({
      key: index,
      slim,
      expandingOrCollapsing,
      onHideMobile,
      onSearchClick,
      currentPath,
      navigate,
    }),
  );

  return (
    <>
      <button
        onClick={onClickOpenCloseToggle}
        aria-label={gettext('Toggle sidebar')}
        aria-expanded={visibleOnMobile ? 'true' : 'false'}
        className={
          'button sidebar-nav-toggle' +
          (isMobile ? ' sidebar-nav-toggle--mobile' : '') +
          (visibleOnMobile ? ' sidebar-nav-toggle--open' : '')
        }
        type="button"
        ref={mobileNavToggleRef}
      >
        {visibleOnMobile ? <Icon name="cross" /> : <Icon name="bars" />}
      </button>
      <div
        className={
          'sidebar' +
          (slim ? ' sidebar--slim' : '') +
          (isMobile ? ' sidebar--mobile' : '') +
          (isMobile && !visibleOnMobile ? ' sidebar--hidden' : '') +
          (isMobile && !visibleOnMobile && closedOnMobile
            ? ' sidebar--closed'
            : '')
        }
      >
        <div
          className="sidebar__inner"
          onFocus={onFocusHandler}
          onBlur={onBlurHandler}
        >
          <div
            className={`sm:w-mt-2 ${
              slim ? 'w-justify-center' : 'w-justify-end'
            } w-flex  w-items-center`}
          >
            <button
              onClick={onClickCollapseToggle}
              aria-label={gettext('Toggle sidebar')}
              aria-expanded={slim ? 'false' : 'true'}
              type="button"
              className={`${!slim ? 'w-mr-4' : ''}
                button
                sidebar__collapse-toggle
                w-flex
                w-justify-center
                w-items-center
                hover:w-bg-primary-200
                hover:text-white
                hover:opacity-100`}
            >
              <Icon
                name="expand-right"
                className={!collapsed ? '-w-rotate-180' : ''}
              />
            </button>
          </div>

          {renderedModules}
        </div>
      </div>
    </>
  );
};
