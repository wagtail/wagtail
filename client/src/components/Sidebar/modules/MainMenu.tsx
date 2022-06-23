import * as React from 'react';

import Tippy from '@tippyjs/react';
import { gettext } from '../../../utils/gettext';
import Icon from '../../Icon/Icon';

import { LinkMenuItemDefinition } from '../menu/LinkMenuItem';
import { MenuItemDefinition } from '../menu/MenuItem';
import { SubMenuItemDefinition } from '../menu/SubMenuItem';
import { ModuleDefinition } from '../Sidebar';

export function renderMenu(
  path: string,
  items: MenuItemDefinition[],
  slim: boolean,
  state: MenuState,
  dispatch: (action: MenuAction) => void,
  navigate: (url: string) => Promise<void>,
) {
  return (
    <>
      {items.map((item) =>
        item.render({
          path: `${path}.${item.name}`,
          slim,
          state,
          dispatch,
          navigate,
        }),
      )}
    </>
  );
}

interface SetActivePath {
  type: 'set-active-path';
  path: string;
}

interface SetNavigationPath {
  type: 'set-navigation-path';
  path: string;
}

export type MenuAction = SetActivePath | SetNavigationPath;

export interface MenuState {
  navigationPath: string;
  activePath: string;
}

function menuReducer(state: MenuState, action: MenuAction) {
  const newState = { ...state };

  if (action.type === 'set-active-path') {
    newState.activePath = action.path;
  } else if (action.type === 'set-navigation-path') {
    newState.navigationPath = action.path;
  }

  return newState;
}

interface MenuProps {
  menuItems: MenuItemDefinition[];
  accountMenuItems: MenuItemDefinition[];
  user: MainMenuModuleDefinition['user'];
  slim: boolean;
  expandingOrCollapsing: boolean;
  onHideMobile: () => void;
  currentPath: string;

  navigate(url: string): Promise<void>;
}

export const Menu: React.FunctionComponent<MenuProps> = ({
  menuItems,
  accountMenuItems,
  user,
  expandingOrCollapsing,
  onHideMobile,
  slim,
  currentPath,
  navigate,
}) => {
  // navigationPath and activePath are two dot-delimited path's referencing a menu item
  // They are created by concatenating the name fields of all the menu/sub-menu items leading to the relevant one.
  // For example, the "Users" item in the "Settings" sub-menu would have the path 'settings.users'
  // - navigationPath references the current sub-menu that the user currently has open
  // - activePath references the menu item for the the page the user is currently on
  const [state, dispatch] = React.useReducer(menuReducer, {
    navigationPath: '',
    activePath: '',
  });
  const isVisible = !slim || expandingOrCollapsing;
  const accountSettingsOpen = state.navigationPath.startsWith('.account');

  React.useEffect(() => {
    // Force account navigation to closed state when in slim mode
    if (slim && accountSettingsOpen) {
      dispatch({
        type: 'set-navigation-path',
        path: '',
      });
    }
  }, [slim]);

  // Whenever currentPath or menu changes, work out new activePath
  React.useEffect(() => {
    const urlPathsToNavigationPaths: [string, string][] = [];
    const walkMenu = (path: string, walkingMenuItems: MenuItemDefinition[]) => {
      walkingMenuItems.forEach((item) => {
        const newPath = `${path}.${item.name}`;

        if (item instanceof LinkMenuItemDefinition) {
          urlPathsToNavigationPaths.push([item.url, newPath]);
        } else if (item instanceof SubMenuItemDefinition) {
          walkMenu(newPath, item.menuItems);
        }
      });
    };

    walkMenu('', menuItems);
    walkMenu('', accountMenuItems);

    let bestMatch: [string, string] | null = null;
    urlPathsToNavigationPaths.forEach(([urlPath, navPath]) => {
      if (currentPath.startsWith(urlPath)) {
        if (bestMatch == null || urlPath.length > bestMatch[0].length) {
          bestMatch = [urlPath, navPath];
        }
      }
    });

    const newActivePath = bestMatch ? bestMatch[1] : '';
    if (newActivePath !== state.activePath) {
      dispatch({
        type: 'set-active-path',
        path: newActivePath,
      });
    }
  }, [currentPath, menuItems]);

  React.useEffect(() => {
    // Close submenus when user presses escape
    const onKeydown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        dispatch({
          type: 'set-navigation-path',
          path: '',
        });

        if (state.navigationPath === '') {
          onHideMobile();
        }
      }
    };

    const onClickOutside = (e: MouseEvent | TouchEvent) => {
      const sidebar = document.querySelector('[data-wagtail-sidebar]');

      const isInside = sidebar && sidebar.contains(e.target as Node);
      if (!isInside) {
        dispatch({
          type: 'set-navigation-path',
          path: '',
        });
      }
    };

    document.addEventListener('keydown', onKeydown);
    document.addEventListener('mousedown', onClickOutside);
    document.addEventListener('touchend', onClickOutside);

    return () => {
      document.removeEventListener('keydown', onKeydown);
      document.removeEventListener('mousedown', onClickOutside);
      document.removeEventListener('touchend', onClickOutside);
    };
  }, []);

  const onClickAccountSettings = () => {
    // Pass account expand information to Sidebar component

    if (accountSettingsOpen) {
      dispatch({
        type: 'set-navigation-path',
        path: '',
      });
    } else {
      dispatch({
        type: 'set-navigation-path',
        path: '.account',
      });
    }
  };

  const className =
    'sidebar-main-menu w-scrollbar-thin' +
    (accountSettingsOpen ? ' sidebar-main-menu--open-footer' : '');

  return (
    <>
      <nav className={className} aria-label={gettext('Main menu')}>
        <ul className="sidebar-main-menu__list">
          {renderMenu('', menuItems, slim, state, dispatch, navigate)}
        </ul>
      </nav>
      <div
        className={
          'sidebar-footer' +
          (accountSettingsOpen ? ' sidebar-footer--open' : '') +
          (isVisible ? ' sidebar-footer--visible' : '')
        }
      >
        <Tippy disabled={!slim} content={user.name} placement="right">
          <button
            className={`
            ${slim ? 'w-px-4' : 'w-px-5'}
            sidebar-footer__account
            w-bg-primary
            w-text-white
            w-flex
            w-items-center
            w-relative
            w-w-full
            w-appearance-none
            w-border-0
            w-overflow-hidden
            w-py-3
            hover:w-bg-primary-200
            focus:w-bg-primary-200
            w-transition`}
            title={gettext('Edit your account')}
            onClick={onClickAccountSettings}
            aria-label={gettext('Edit your account')}
            aria-haspopup="menu"
            aria-expanded={accountSettingsOpen ? 'true' : 'false'}
            type="button"
          >
            <div className="avatar avatar-on-dark w-flex-shrink-0 !w-w-[28px] !w-h-[28px]">
              <img src={user.avatarUrl} alt="" />
            </div>
            <div className="sidebar-footer__account-toggle">
              <div className="sidebar-footer__account-label w-label-3">
                {user.name}
              </div>
              <Icon
                className="w-w-4 w-h-4 w-text-white"
                name={accountSettingsOpen ? 'arrow-down' : 'arrow-up'}
              />
            </div>
          </button>
        </Tippy>

        <ul>
          {renderMenu('', accountMenuItems, slim, state, dispatch, navigate)}
        </ul>
      </div>
    </>
  );
};

export class MainMenuModuleDefinition implements ModuleDefinition {
  menuItems: MenuItemDefinition[];
  accountMenuItems: MenuItemDefinition[];
  user: {
    name: string;
    avatarUrl: string;
  };

  constructor(
    menuItems: MenuItemDefinition[],
    accountMenuItems: MenuItemDefinition[],
    user: MainMenuModuleDefinition['user'],
  ) {
    this.menuItems = menuItems;
    this.accountMenuItems = accountMenuItems;
    this.user = user;
  }

  render({
    slim,
    expandingOrCollapsing,
    onHideMobile,
    key,
    currentPath,
    navigate,
  }) {
    return (
      <Menu
        menuItems={this.menuItems}
        accountMenuItems={this.accountMenuItems}
        user={this.user}
        slim={slim}
        expandingOrCollapsing={expandingOrCollapsing}
        onHideMobile={onHideMobile}
        key={key}
        currentPath={currentPath}
        navigate={navigate}
      />
    );
  }
}
