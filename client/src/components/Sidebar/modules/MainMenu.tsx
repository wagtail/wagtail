/* eslint-disable react/prop-types */

import React from 'react';
import styled, { css } from 'styled-components';

import * as mixins from '../common/mixins';
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

interface MainNavProps {
    collapsed: boolean;
    fullyExpanded: boolean;
    openFooter: boolean;
}

const MainNav = styled.nav<MainNavProps>`
    overflow: auto;
    margin-bottom: ${(props: MainNavProps) => (
    props.openFooter
      ? '127px' /* $nav-footer-open-height */
      : '50px' /* $nav-footer-closed-height */
  )};
    opacity: 1;

    ${mixins.transition('margin-bottom 0.3s ease')}

    ul,
    li {
        margin: 0;
        padding: 0;
        list-style-type: none;
    }

    li {
        ${mixins.transition('border-color 0.3s ease')}
        position: relative;
    }

    a {
        ${mixins.transition('border-color 0.3s ease')}
        -webkit-font-smoothing: auto;
        text-decoration: none;
        display: block;
        color: #ccc;  // $color-menu-text;
        padding: 0.8em 1.7em;
        font-size: 1em;
        font-weight: normal;
        // Note, font-weights lower than normal,
        // and font-size smaller than 1em (80% ~= 12.8px),
        // makes the strokes thinner than 1px on non-retina screens
        // making the text semi-transparent
        &:hover,
        &:focus {
            background-color: rgba(100, 100, 100, 0.15);  // $nav-item-hover-bg;
            color: #fff;  // $color-white
            text-shadow: -1px -1px 0 rgba(0, 0, 0, 0.3);
        }
    }

    *:focus {
        ${mixins.showFocusOutlineInside()}
    }

    .icon--menuitem {
        width: 1.25em;
        height: 1.25em;
        margin-right: 0.5em;
        vertical-align: text-top;
    }

    .icon--submenu-header {
        display: block;
        width: 4rem;
        height: 4rem;
        margin: 0 auto 0.8em;
        opacity: 0.15;
    }

    > ul > li > a {
        // Need !important to override body.ready class
        transition: padding 0.3s ease !important;

        .menuitem-label {
            transition: opacity 0.3s ease;
        }
    }

    ${(props) => props.collapsed && css`
        > ul > li > a {
            padding: 0.8em 0.8em;

            .menuitem-label {
                opacity: 0;
            }

            .icon-arrow-right {
                top: 1.0em;
                right: 0.15em;
                width: 1em;
                height:1em;
            }
        }
    `}

    ${(props) => !props.fullyExpanded && css`
        overflow-x: hidden;
    `}
`;

interface FooterWrapperProps {
    collapsed: boolean;
    isOpen: boolean;
}

const FooterWrapper = styled.li<FooterWrapperProps>`
    position: fixed !important;  // override li styling in MenuWrapper
    width: 200px;  // $menu-width;
    bottom: 0;
    background-color: #262626;  // $nav-footer-submenu-bg;
    transition: width 0.3s ease !important;  // Override body.ready

    ${(props) => (props.collapsed && !props.isOpen) && css`
        width: 50px;
    `}

    > ul {
        ${mixins.transition('max-height 0.3s ease')}

        max-height: ${(props: FooterWrapperProps) => (props.isOpen ? '77px' /* $nav-footer-submenu-height */: '0')};

        a {
            border-left: 3px solid transparent;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;

            &:before {
                font-size: 1rem;
                margin-right: 0.5em;
                vertical-align: -10%;
            }
        }
    }

    .account {
        ${mixins.clearfix()}
        background: #1a1a1a;  // $nav-footer-account-bg;
        color: #ccc;  // $color-menu-text;
        text-transform: uppercase;
        display: block;
        cursor: pointer;
        position: relative;

        &:hover {
            background-color: rgba(100, 100, 100, 0.15);
            color: #fff;  // $color-white
            text-shadow: -1px -1px 0 rgba(0, 0, 0, 0.3);
        }

        .avatar {
            float: left;

            &:before {
                color: inherit;
                border-color: inherit;
            }
        }

        em {
            box-sizing: border-box;
            padding-right: 1.8em;
            margin-top: 1.2em;
            margin-left: 0.9em;
            font-style: normal;
            font-weight: 700;
            width: 135px;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            position: absolute;
            left: 50px;  // Width of avatar
            transition: left 0.3s ease;

            ${(props) => (props.collapsed && !props.isOpen) && css`
                left: -150px;  // menu closed with - menu open width
            `}

            &:after {
                font-size: 1.5em;
                position: absolute;
                right: 0.25em;
            }
        }
    }
`;

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
  // esline-disable-next-line consistent-return
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
    <MainNav collapsed={collapsed} fullyExpanded={fullyExpanded} openFooter={accountSettingsOpen}>
      <ul>
        {renderMenu('', menuItems, state, dispatch, collapsed, navigate)}

        <FooterWrapper collapsed={collapsed} isOpen={accountSettingsOpen}>
          <div className="account" title={'Edit your account'} onClick={onClickAccountSettings}>{/* GETTEXT */}
            <span className="avatar square avatar-on-dark">
              <img src={user.avatarUrl} alt="" />
            </span>
            <em className={'icon ' + (accountSettingsOpen ? 'icon-arrow-down-after' : 'icon-arrow-up-after')}>{user.name}</em>
          </div>

          <ul>
            {renderMenu('', accountMenuItems, state, dispatch, collapsed, navigate)}
          </ul>
        </FooterWrapper>
      </ul>
    </MainNav>
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
