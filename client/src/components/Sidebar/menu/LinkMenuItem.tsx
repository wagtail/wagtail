/* eslint-disable react/prop-types */

import React from 'react';

import Icon from '../common/Icon';
import { MenuItemDefinition, MenuItemProps, MenuItemWrapper } from './MenuItem';

export const LinkMenuItem: React.FunctionComponent<MenuItemProps<LinkMenuItemDefinition>> = (
  { item, path, state, dispatch, navigate }) => {
  const isActive = state.activePath.startsWith(path);
  const isInSubmenu = path.split('.').length > 2;

  const onClick = (e: React.MouseEvent) => {
    e.preventDefault();

    navigate(item.url).then(() => {
      // Set active menu item
      dispatch({
        type: 'set-active-path',
        path,
      });

      // Reset navigation path to close any open submenus
      dispatch({
        type: 'set-navigation-path',
        path: '',
      });
    });
  };

  return (
    <MenuItemWrapper isActive={isActive} isInSubmenu={isInSubmenu}>
      <a href="#" onClick={onClick} className={item.classNames}>
        {item.iconName && <Icon name={item.iconName} className="icon--menuitem" />}
        <span className="menuitem-label">{item.label}</span>
      </a>
    </MenuItemWrapper>
  );
};

export class LinkMenuItemDefinition implements MenuItemDefinition {
    name: string;
    label: string;
    url: string;
    iconName: string | null;
    classNames?: string;

    constructor({ name, label, url, icon_name: iconName = null, classnames = undefined }) {
      this.name = name;
      this.label = label;
      this.url = url;
      this.iconName = iconName;
      this.classNames = classnames;
    }

    render({ path, state, collapsed, dispatch, navigate }) {
      return <LinkMenuItem key={this.name} item={this} path={path} state={state} collapsed={collapsed} dispatch={dispatch} navigate={navigate} />;
    }
}
