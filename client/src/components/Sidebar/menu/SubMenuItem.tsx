/* eslint-disable react/prop-types */

import * as React from 'react';

import Icon from '../common/Icon';

import { renderMenu } from '../modules/MainMenu';
import { MenuItemDefinition, MenuItemProps } from './MenuItem';

interface SubMenuItemProps extends MenuItemProps<SubMenuItemDefinition> {
  slim: boolean;
}

export const SubMenuItem: React.FunctionComponent<SubMenuItemProps> = (
  { path, item, slim, state, dispatch, navigate }) => {
  const isOpen = state.navigationPath.startsWith(path);
  const isActive = isOpen || state.activePath.startsWith(path);
  const depth = path.split('.').length;
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
      }, 150);
    }
  }, [isOpen]);

  const onClick = (e: React.MouseEvent) => {
    if (isOpen) {
      const pathComponents = path.split('.');
      pathComponents.pop();
      const parentPath = pathComponents.join('.');
      dispatch({
        type: 'set-navigation-path',
        path: parentPath,
      });
    } else {
      dispatch({
        type: 'set-navigation-path',
        path,
      });
    }

    e.preventDefault();
  };

  const className = (
    'sidebar-menu-item sidebar-sub-menu-item'
    + (isActive ? ' sidebar-menu-item--active' : '')
    + (isOpen ? ' sidebar-sub-menu-item--open' : '')
  );

  const sidebarTriggerIconClassName = (
    'sidebar-sub-menu-trigger-icon'
    + (isOpen ? ' sidebar-sub-menu-trigger-icon--open' : '')
  );

  const sidebarSubMenuPanelClassName = (
    'sidebar-sub-menu-panel'
    + (isVisible ? ' sidebar-sub-menu-panel--visible' : '')
    + (isOpen ? ' sidebar-sub-menu-panel--open' : '')
  );

  return (
    <li className={className}>
      <a
        href="#"
        onClick={onClick}
        className={`sidebar-menu-item__link ${item.classNames}`}
        aria-haspopup="true"
        aria-expanded={isOpen ? 'true' : 'false'}
      >
        {item.iconName && <Icon name={item.iconName} className="icon--menuitem" />}
        <span className="menuitem-label">{item.label}</span>
        <Icon className={sidebarTriggerIconClassName} name="arrow-right" />
      </a>
      <div className={sidebarSubMenuPanelClassName} style={{ zIndex: -depth }}>
        <p id={`wagtail-sidebar-submenu${path.split('.').join('-')}-title`} className={item.classNames}>
          {item.iconName && <Icon name={item.iconName} className="icon--submenu-header" />}
          {item.label}
        </p>
        <ul aria-labelledby={`wagtail-sidebar-submenu${path.split('.').join('-')}-title`}>
          {renderMenu(path, item.menuItems, slim, state, dispatch, navigate)}
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

  constructor(
    {
      name,
      label,
      icon_name: iconName = null,
      classnames = undefined
    }: any,
    menuItems: MenuItemDefinition[]
  ) {
    this.name = name;
    this.label = label;
    this.menuItems = menuItems;
    this.iconName = iconName;
    this.classNames = classnames;
  }

  render({ path, slim, state, dispatch, navigate }) {
    return (
      <SubMenuItem
        key={this.name}
        item={this}
        path={path}
        slim={slim}
        state={state}
        dispatch={dispatch}
        navigate={navigate}
      />
    );
  }
}

export class SettingsMenuItemDefinition extends SubMenuItemDefinition {
}
