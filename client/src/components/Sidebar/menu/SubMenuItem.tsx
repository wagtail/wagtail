/* eslint-disable react/prop-types */

import React from 'react';
import styled, { css } from 'styled-components';

import Icon, { IconProps } from '../common/Icon';
import * as mixins from '../common/mixins';

import { renderMenu } from '../modules/MainMenu';
import { MenuItemDefinition, MenuItemProps, MenuItemWrapper, MenuItemWrapperProps } from './MenuItem';


export interface SubMenuItemTriggerIconProps extends IconProps {
    isOpen: boolean
}
export const SubMenuItemTriggerIcon = styled<React.FunctionComponent<SubMenuItemTriggerIconProps>>(Icon)`
    display: block;
    width: 1.5em;
    height: 1.5em;
    position: absolute;
    top: 0.8125em;
    right: 0.5em;
    ${mixins.transition('transform 0.3s ease, top 0.3s ease, right 0.3s ease, width 0.3s ease, height 0.3s ease')}

    ${(props) => props.isOpen && css`
        transform-origin: 50% 50%;
        transform: rotate(180deg);
    `}
`;

export interface SubMenuPanelWrapperProps {
    // isVisible can be true while isOpen is false when the menu is closing
    isVisible: boolean;
    isOpen: boolean;
    collapsed: boolean;
}

export const SubMenuPanelWrapper = styled.div<SubMenuPanelWrapperProps>`
    visibility: hidden;
    background: #262626;  // $nav-submenu-bg;
    z-index: -2;
    transform: translate3d(0, 0, 0);
    position: fixed;
    height: 100vh;
    width: 200px;  // $menu-width;
    padding: 0;
    top: 0;
    left: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;

    ${mixins.transition('left 0.3s ease')}

    h2,
    &__list {
        width: 200px;  // $menu-width;
    }

    h2 {
        display: block;
        padding: 0.2em 0;
        font-size: 1.2em;
        font-weight: 500;
        text-transform: none;
        text-align: center;
        color: #ccc;  // $color-menu-text;

        &:before {
            font-size: 4em;
            display: block;
            text-align: center;
            margin: 0 0 0.2em;
            width: 100%;
            opacity: 0.15;
        }
    }

    ul {
        overflow: auto;
        flex-grow: 1;
    }

    li {
        border: 0;
    }

    &__footer {
        margin: 0;
        text-align: center;
        color: #ccc;  // $color-menu-text;
        line-height: 50px;  // $nav-footer-closed-height;
        padding: 0;
    }

    ${(props) => props.isVisible && css`
        visibility: visible;
        box-shadow: 2px 0 2px rgba(0, 0, 0, 0.35);

        a {
            padding-left: 3.5em;
        }
    `}

    ${(props) => props.collapsed && css`
        left: -150px;  // Slim menu width minus submenu width
    `}

    ${(props) => props.isOpen && css`
        left: 200px;  // Menu width

        // If another submenu is opening, display this menu behind it
        z-index: -1;
    `}

    ${(props) => props.isOpen && props.collapsed && css`
        left: 50px;  // Slim menu width
    `}
`;

export interface SubMenuItemWrapperProps extends MenuItemWrapperProps {
    isOpen: boolean;
}

export const SubMenuItemWrapper = styled(MenuItemWrapper)<SubMenuItemWrapperProps>`
    ${(props) => props.isOpen && css`
        background: #262626;  // $nav-submenu-bg;

        > a {
            text-shadow: -1px -1px 0 rgba(0, 0, 0, 0.3);

            &:hover {
                background-color: transparent;
            }
        }
    `}
`;

export const SubMenuItem: React.FunctionComponent<MenuItemProps<SubMenuItemDefinition>> = (
  { path, item, state, dispatch, collapsed, navigate }) => {
  const isOpen = state.navigationPath.startsWith(path);
  const isActive = isOpen || state.activePath.startsWith(path);
  const [isVisible, setIsVisible] = React.useState(false);

  React.useEffect(() => {
    if (isOpen) {
      // isOpen is set at the moment the user clicks the menu item
      setIsVisible(true);
    } else if (!isOpen && isVisible) {
      // When a submenu is closed, we have to wait for the close animation
      // to finish before making it invisible
      setTimeout(() => {
        setIsVisible(false);
      }, 300);
    }
  }, [isOpen]);

  const onClick = (e: React.MouseEvent) => {
    if (isOpen) {
      dispatch({
        type: 'set-navigation-path',
        path: '',
      });
    } else {
      dispatch({
        type: 'set-navigation-path',
        path,
      });
    }

    e.preventDefault();
  };

  return (
    <SubMenuItemWrapper isActive={isActive} isInSubmenu={false} isOpen={isOpen}>
      <a
        href="#"
        onClick={onClick}
        className={item.classNames}
        aria-haspopup="true"
        aria-expanded={isOpen ? 'true' : 'false'}
      >
        {item.iconName && <Icon name={item.iconName} className="icon--menuitem" />}
        <span className="menuitem-label">{item.label}</span>
        <SubMenuItemTriggerIcon name="arrow-right" isOpen={isOpen} />
      </a>
      <SubMenuPanelWrapper isVisible={isVisible} isOpen={isOpen} collapsed={collapsed}>
        <h2 id={`nav-submenu-${item.name}-title`} className={item.classNames}>
          {item.iconName && <Icon name={item.iconName} className="icon--submenu-header" />}
          {item.label}
        </h2>
        <ul aria-labelledby="nav-submenu-{{ name }}-title">
          {renderMenu(path, item.menuItems, state, dispatch, collapsed, navigate)}
        </ul>
      </SubMenuPanelWrapper>
    </SubMenuItemWrapper>
  );
};

export class SubMenuItemDefinition implements MenuItemDefinition {
    name: string;
    label: string;
    menuItems: MenuItemDefinition[];
    iconName: string | null;
    classNames?: string

    constructor({ name, label, icon_name: iconName = null, classnames = undefined }: any, menuItems: MenuItemDefinition[]) {
      this.name = name;
      this.label = label;
      this.menuItems = menuItems;
      this.iconName = iconName;
      this.classNames = classnames;
    }

    render({ path, state, collapsed, dispatch, navigate }) {
      return <SubMenuItem key={this.name} item={this} path={path} state={state} collapsed={collapsed} dispatch={dispatch} navigate={navigate} />;
    }
}

export class SettingsMenuItemDefinition extends SubMenuItemDefinition {
}
