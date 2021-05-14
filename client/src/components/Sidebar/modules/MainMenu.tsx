/* eslint-disable react/prop-types */

import React from 'react';

import { LinkMenuItemDefinition } from '../menu/LinkMenuItem';
import { MenuItemDefinition } from '../menu/MenuItem';
import { SubMenuItemDefinition } from '../menu/SubMenuItem';
import { ModuleDefinition } from '../Sidebar';

export function renderMenu(
  path: string,
  items: MenuItemDefinition[],
  state: MenuState,
  dispatch: (action: MenuAction) => void,
  collapsed: boolean,
  navigate: (url: string) => Promise<void>
) {
  return (
    <>
      {items.map(item => item.render({
        path: `${path}.${item.name}`,
        collapsed,
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
    collapsed: boolean;
    activeUrl: string;
    menuItems: MenuItemDefinition[];
    accountMenuItems: MenuItemDefinition[];
    user: MainMenuModuleDefinition['user'];
    navigate(url: string): Promise<void>;
}

export const Menu: React.FunctionComponent<MenuProps> = (
  { collapsed, activeUrl, menuItems, accountMenuItems, user, navigate }) => {
  const [state, dispatch] = React.useReducer(menuReducer, {
    navigationPath: '',
    activePath: '',
  });
  const accountSettingsOpen = state.navigationPath.startsWith('.account');

  // Whenever activeUrl or menu changes, work out new activePath
  React.useEffect(() => {
    const urlToPaths: [string, string][] = [];
    const walkMenu = (path: string, walkingMenuItems: MenuItemDefinition[]) => {
      walkingMenuItems.forEach((item) => {
        const newPath = `${path}.${item.name}`;

        if (item instanceof LinkMenuItemDefinition) {
          urlToPaths.push([item.url, newPath]);
        } else if (item instanceof SubMenuItemDefinition) {
          walkMenu(newPath, item.menuItems);
        }
      });
    };

    walkMenu('', menuItems);

    let bestMatch: [string, string] | null = null;
    urlToPaths.forEach(([url, path]) => {
      if (activeUrl.startsWith(url)) {
        if (bestMatch == null || url.length > bestMatch[0].length) {
          bestMatch = [url, path];
        }
      }
    });

    const newActivePath = bestMatch ? bestMatch[1] : '';

    // TODO: Probably doesn't have to be in state anymore
    if (newActivePath !== state.activePath) {
      dispatch({
        type: 'set-active-path',
        path: newActivePath,
      });
    }
  }, [activeUrl, menuItems]);

  // const activeClass = 'submenu-active';
  // const submenuContainerRef = React.useRef<HTMLLIElement | null>(null);
  React.useEffect(() => {
    /* TODO
        // Close submenu when user clicks outside of it
        // FIXME: Doesn't actually work because outside click events are usually in an iframe.
        const onMousedown = (e: MouseEvent) => {
            if (e.target instanceof HTMLElement && submenuContainerRef.current && !submenuContainerRef.current.contains(e.target)) {
                //dispatch({
                //    type: 'close-submenu',
                //});
            }
        };
*/

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

    // document.addEventListener('mousedown', onMousedown);
    document.addEventListener('keydown', onKeydown);

    return () => {
      // document.removeEventListener('mousedown', onMousedown);
      document.removeEventListener('keydown', onKeydown);
    };
  }, []);

  // Whenever the menu is uncollapsed, wait until it has fully expanded before adding the `overflow: auto` rule back
  // This prevents an ugly flash of the scrollbar while the animation is in progress
  const [fullyExpanded, setFullyExpanded] = React.useState(collapsed);
  // eslint-disable-next-line consistent-return
  React.useEffect(() => {
    if (collapsed) {
      setFullyExpanded(false);
    }
    if (!collapsed && !fullyExpanded) {
      const timeout = setTimeout(() => {
        setFullyExpanded(true);
      }, 300);
      return () => clearTimeout(timeout);
    }
  }, [collapsed]);

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

  return (
    <nav className={'sidebar-main-menu' + (fullyExpanded ? ' sidebar-main-menu--fully-expanded' : '') + (accountSettingsOpen ? ' sidebar-main-menu--open-footer' : '')}>
      <ul>
        {renderMenu('', menuItems, state, dispatch, collapsed, navigate)}

        <li className={'sidebar-footer' + (accountSettingsOpen ? ' sidebar-footer--open' : '')}>
          <div className="sidebar-footer__account" title={'Edit your account'} onClick={onClickAccountSettings}>{/* GETTEXT */}
            <span className="avatar square avatar-on-dark">
              <img src={user.avatarUrl} alt="" />
            </span>
            <em className={'icon ' + (accountSettingsOpen ? 'icon-arrow-down-after' : 'icon-arrow-up-after')}>{user.name}</em>
          </div>

          <ul>
            {renderMenu('', accountMenuItems, state, dispatch, collapsed, navigate)}
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

    constructor(menuItems: MenuItemDefinition[], accountMenuItems: MenuItemDefinition[], user: MainMenuModuleDefinition['user']) {
      this.menuItems = menuItems;
      this.accountMenuItems = accountMenuItems;
      this.user = user;
    }

    render({ collapsed, navigate, currentPath }) {
      return <Menu collapsed={collapsed} activeUrl={currentPath} menuItems={this.menuItems} accountMenuItems={this.accountMenuItems} user={this.user} navigate={navigate} />;
    }
}
