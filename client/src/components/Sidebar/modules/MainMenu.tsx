/* eslint-disable react/prop-types */

import * as React from 'react';
import Icon from '../../Icon/Icon';

import { LinkMenuItemDefinition } from '../menu/LinkMenuItem';
import { MenuItemDefinition } from '../menu/MenuItem';
import { SubMenuItemDefinition } from '../menu/SubMenuItem';
import { ModuleDefinition, Strings } from '../Sidebar';

export function renderMenu(
  path: string,
  items: MenuItemDefinition[],
  slim: boolean,
  state: MenuState,
  dispatch: (action: MenuAction) => void,
  navigate: (url: string) => Promise<void>
) {
  return (
    <>
      {items.map(item => item.render({
        path: `${path}.${item.name}`,
        slim,
        state,
        dispatch,
        navigate,
      }))}
    </>
  );
}

interface SetActivePath {
  type: 'set-active-path',
  path: string,
}

interface SetNavigationPath {
  type: 'set-navigation-path',
  path: string,
}

export type MenuAction = SetActivePath | SetNavigationPath;

export interface MenuState {
  navigationPath: string;
  activePath: string;
}

function menuReducer(state: MenuState, action: MenuAction) {
  const newState = Object.assign({}, state);

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
  currentPath: string;
  strings: Strings;
  navigate(url: string): Promise<void>;
}

export const Menu: React.FunctionComponent<MenuProps> = (
  { menuItems, accountMenuItems, user, expandingOrCollapsing, slim, currentPath, strings, navigate }) => {
  // navigationPath and activePath are two dot-delimited path's referencing a menu item
  // They are created by concatenating the name fields of all the menu/sub-menu items leading to the relevant one.
  // For example, the "Users" item in the "Settings" sub-menu would have the path 'settings.users'
  // - navigationPath references the current sub-menu that the user currently has open
  // - activePath references the menu item for the the page the user is currently on
  const [state, dispatch] = React.useReducer(menuReducer, {
    navigationPath: '',
    activePath: '',
  });
  const accountSettingsOpen = state.navigationPath.startsWith('.account');

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
      // IE11 uses "Esc" instead of "Escape"
      if (e.key === 'Escape' || e.key === 'Esc') {
        dispatch({
          type: 'set-navigation-path',
          path: ''
        });
      }
    };

    document.addEventListener('keydown', onKeydown);

    return () => {
      document.removeEventListener('keydown', onKeydown);
    };
  }, []);

  // Whenever the parent Sidebar component collapses or expands, close any open menus
  React.useEffect(() => {
    if (expandingOrCollapsing) {
      dispatch({
        type: 'set-navigation-path',
        path: ''
      });
    }
  }, [expandingOrCollapsing]);

  const onClickAccountSettings = (e: React.MouseEvent) => {
    e.preventDefault();

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

  const className = (
    'sidebar-main-menu'
    + (accountSettingsOpen ? ' sidebar-main-menu--open-footer' : '')
  );

  return (
    <nav className={className}>
      <ul className="sidebar-main-menu__list">
        {renderMenu('', menuItems, slim, state, dispatch, navigate)}

        <li className={'sidebar-footer' + (accountSettingsOpen ? ' sidebar-footer--open' : '')}>
          <div
            className="sidebar-footer__account"
            title={strings.EDIT_YOUR_ACCOUNT}
            onClick={onClickAccountSettings}
          >
            <span className="avatar square avatar-on-dark">
              <img src={user.avatarUrl} alt="" />
            </span>
            <em>
              {user.name}
              <Icon
                className="sidebar-footer__account--icon"
                name={(accountSettingsOpen ? 'arrow-down' : 'arrow-up')}
              />
            </em>
          </div>

          <ul>
            {renderMenu('', accountMenuItems, slim, state, dispatch, navigate)}
          </ul>
        </li>
      </ul>
    </nav>
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
    user: MainMenuModuleDefinition['user']
  ) {
    this.menuItems = menuItems;
    this.accountMenuItems = accountMenuItems;
    this.user = user;
  }

  render({ slim, expandingOrCollapsing, key, currentPath, strings, navigate }) {
    return (
      <Menu
        menuItems={this.menuItems}
        accountMenuItems={this.accountMenuItems}
        user={this.user}
        slim={slim}
        expandingOrCollapsing={expandingOrCollapsing}
        key={key}
        currentPath={currentPath}
        strings={strings}
        navigate={navigate}
      />
    );
  }
}
