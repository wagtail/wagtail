/* eslint-disable react/prop-types */

import React from 'react';

import Icon from '../common/Icon';

import { renderMenu } from '../modules/MainMenu';
import { MenuItemDefinition, MenuItemProps } from './MenuItem';

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
    <li className={'sidebar-menu-item sidebar-sub-menu-item' + (isActive ? ' sidebar-menu-item--active' : '') + (isOpen ? ' sidebar-sub-menu-item--open' : '')}>
      <a
        href="#"
        onClick={onClick}
        className={item.classNames}
        aria-haspopup="true"
        aria-expanded={isOpen ? 'true' : 'false'}
      >
        {item.iconName && <Icon name={item.iconName} className="icon--menuitem" />}
        <span className="menuitem-label">{item.label}</span>
        <Icon className={'sidebar-sub-menu-trigger-icon' + (isOpen ? ' sidebar-sub-menu-trigger-icon--open' : '')} name="arrow-right" />
      </a>
      <div className={'sidebar-sub-menu-panel' + (isVisible ? ' sidebar-sub-menu-panel--visible' : '') + (isOpen ? ' sidebar-sub-menu-panel--open' : '')}>
        <h2 id={`nav-submenu-${item.name}-title`} className={item.classNames}>
          {item.iconName && <Icon name={item.iconName} className="icon--submenu-header" />}
          {item.label}
        </h2>
        <ul aria-labelledby="nav-submenu-{{ name }}-title">
          {renderMenu(path, item.menuItems, state, dispatch, collapsed, navigate)}
        </ul>
      </div>
    </li>
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
