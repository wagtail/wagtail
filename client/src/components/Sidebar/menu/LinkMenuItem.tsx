import * as React from 'react';

import Tippy from '@tippyjs/react';
import Icon from '../../Icon/Icon';
import { MenuItemDefinition, MenuItemProps } from './MenuItem';

export const LinkMenuItem: React.FunctionComponent<
  MenuItemProps<LinkMenuItemDefinition>
> = ({ item, slim, path, state, dispatch, navigate }) => {
  const isCurrent = state.activePath === path;
  const isActive = state.activePath.startsWith(path);
  const isInSubMenu = path.split('.').length > 2;

  const onClick = (e: React.MouseEvent) => {
    // Do not capture click events with modifier keys or non-main buttons.
    if (e.ctrlKey || e.shiftKey || e.metaKey || (e.button && e.button !== 0)) {
      return;
    }

    // For compatibility purposes – do not capture clicks for links with a target.
    if (item.attrs && item.attrs.target) {
      return;
    }

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

  const className =
    'sidebar-menu-item' +
    (isActive ? ' sidebar-menu-item--active' : '') +
    (isInSubMenu ? ' sidebar-menu-item--in-sub-menu' : '');

  return (
    <li className={className}>
      <Tippy
        disabled={!slim || isInSubMenu}
        content={item.label}
        placement="right"
      >
        <a
          {...item.attrs}
          href={item.url}
          aria-current={isCurrent ? 'page' : undefined}
          onClick={onClick}
          className={`sidebar-menu-item__link ${item.classNames}`}
        >
          {item.iconName && (
            <Icon name={item.iconName} className="icon--menuitem" />
          )}
          <span className="menuitem-label">{item.label}</span>
        </a>
      </Tippy>
    </li>
  );
};

export class LinkMenuItemDefinition implements MenuItemDefinition {
  name: string;
  label: string;
  url: string;
  iconName: string | null;
  classNames?: string;
  attrs: { [key: string]: any } | null;

  constructor({
    name,
    label,
    url,
    icon_name: iconName = null,
    classnames = undefined,
    attrs = null,
  }) {
    this.name = name;
    this.label = label;
    this.url = url;
    this.iconName = iconName;
    this.classNames = classnames;
    this.attrs = attrs;
  }

  render({ path, slim, state, dispatch, navigate }) {
    return (
      <LinkMenuItem
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
