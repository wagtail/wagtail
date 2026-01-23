import * as React from 'react';

import Tippy from '@tippyjs/react';
import Icon from '../../Icon/Icon';
import { MenuItemDefinition, MenuItemProps } from './MenuItem';
import { gettext } from '../../../utils/gettext';
import { isDismissed } from '../modules/MainMenu';
import { WAGTAIL_CONFIG } from '../../../config/wagtailConfig';

export const ActionMenuItem: React.FunctionComponent<
  MenuItemProps<ActionMenuItemDefinition>
> = ({ item, slim, path, state, dispatch }) => {
  const isActive = state.activePath.startsWith(path);
  const isInSubMenu = path.split('.').length > 2;

  const onClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    // Do not capture click events with modifier keys or non-main buttons.
    if (e.ctrlKey || e.shiftKey || e.metaKey || (e.button && e.button !== 0)) {
      return;
    }

    if (!isDismissed(item, state)) {
      dispatch({
        type: 'set-dismissible-state',
        item,
      });
    }
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
        <form {...item.attrs} method={item.method} action={item.action}>
          <input
            type="hidden"
            name="csrfmiddlewaretoken"
            value={WAGTAIL_CONFIG.CSRF_TOKEN}
          />
          <button
            type="submit"
            className={`sidebar-menu-item__link ${item.classNames}`}
            onClick={onClick}
          >
            {item.iconName && (
              <Icon name={item.iconName} className="icon--menuitem" />
            )}
            <span className="menuitem">
              <span className="menuitem-label">{item.label}</span>
              {!isDismissed(item, state) && (
                <span className="w-dismissible-badge">
                  <span className="w-sr-only">{gettext('(New)')}</span>
                </span>
              )}
            </span>
          </button>
        </form>
      </Tippy>
    </li>
  );
};

export class ActionMenuItemDefinition implements MenuItemDefinition {
  name: string;
  label: string;
  action: string;
  attrs: { [key: string]: any };
  iconName: string | null;
  classNames?: string;
  method: string;

  constructor({
    name,
    label,
    action,
    attrs = {},
    icon_name: iconName = null,
    classname = undefined,
    method = 'POST',
  }) {
    this.name = name;
    this.label = label;
    this.action = action;
    this.attrs = attrs;
    this.iconName = iconName;
    this.classNames = classname;
    this.method = method;
  }

  render({ path, slim, state, dispatch, navigate }) {
    return (
      <ActionMenuItem
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
