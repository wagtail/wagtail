/* eslint-disable react/prop-types */

import * as React from 'react';

import Icon from '../../Icon/Icon';
import { MenuItemDefinition, MenuItemProps } from './MenuItem';

export const LinkMenuItem: React.FunctionComponent<MenuItemProps<LinkMenuItemDefinition>> = (
  { item, path, state, dispatch, navigate }) => {
  const isActive = state.activePath.startsWith(path);
  const isInSubMenu = path.split('.').length > 2;

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

  const className = (
    'sidebar-menu-item'
    + (isActive ? ' sidebar-menu-item--active' : '')
    + (isInSubMenu ? ' sidebar-menu-item--in-sub-menu' : '')
  );

  const [peeking, setPeeking] = React.useState(false);
  const wrapperRef = React.useRef<HTMLLIElement | null>(null);
  React.useEffect(() => {
    if (!wrapperRef.current) {
      return;
    }

    const element = wrapperRef.current;
    let startPeekingTimeout;
    let stopPeekingTimeout;

    const onMouseEnterHandler = () => {
      clearTimeout(startPeekingTimeout);
      clearTimeout(stopPeekingTimeout);
      startPeekingTimeout = setTimeout(() => {
        setPeeking(true);
      }, 250);
    };

    const onMouseLeaveHandler = () => {
      clearTimeout(startPeekingTimeout);
      clearTimeout(stopPeekingTimeout);
      stopPeekingTimeout = setTimeout(() => {
        setPeeking(false);
      }, 250);
    };

    element.addEventListener('mouseenter', onMouseEnterHandler);
    element.addEventListener('mouseleave', onMouseLeaveHandler);
  }, []);

  return (
    <li className={className} ref={wrapperRef}>
      <a href="#" onClick={onClick} className={`sidebar-menu-item__link ${item.classNames}`}>
        {item.iconName && <Icon name={item.iconName} className="icon--menuitem" />}
        <span className="menuitem-label">{item.label}</span>
        <div className={'menuitem-tooltip' + (peeking ? ' menuitem-tooltip--visible' : '')}>
          <div className="menuitem-tooltip__inner">
            {item.label}
          </div>
        </div>
      </a>
    </li>
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

  render({ path, state, dispatch, navigate }) {
    return (
      <LinkMenuItem
        key={this.name}
        item={this}
        path={path}
        state={state}
        dispatch={dispatch}
        navigate={navigate}
      />
    );
  }
}
