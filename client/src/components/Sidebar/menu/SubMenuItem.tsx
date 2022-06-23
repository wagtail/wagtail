import * as React from 'react';

import Tippy from '@tippyjs/react';
import Icon from '../../Icon/Icon';

import { renderMenu } from '../modules/MainMenu';
import { SidebarPanel } from '../SidebarPanel';
import { SIDEBAR_TRANSITION_DURATION } from '../Sidebar';
import { MenuItemDefinition, MenuItemProps } from './MenuItem';

interface SubMenuItemProps extends MenuItemProps<SubMenuItemDefinition> {
  slim: boolean;
}

export const SubMenuItem: React.FunctionComponent<SubMenuItemProps> = ({
  path,
  item,
  slim,
  state,
  dispatch,
  navigate,
}) => {
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
      }, SIDEBAR_TRANSITION_DURATION);
    }
  }, [isOpen]);

  const onClick = () => {
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
  };

  const className =
    'sidebar-menu-item sidebar-sub-menu-item' +
    (isActive ? ' sidebar-menu-item--active' : '') +
    (isOpen ? ' sidebar-sub-menu-item--open' : '');

  const sidebarTriggerIconClassName =
    'sidebar-sub-menu-trigger-icon' +
    (isOpen ? ' sidebar-sub-menu-trigger-icon--open' : '');

  return (
    <li className={className}>
      <Tippy disabled={isOpen || !slim} content={item.label} placement="right">
        <button
          onClick={onClick}
          className={`sidebar-menu-item__link ${item.classNames}`}
          aria-haspopup="menu"
          aria-expanded={isOpen ? 'true' : 'false'}
          type="button"
        >
          {item.iconName && (
            <Icon name={item.iconName} className="icon--menuitem" />
          )}
          <span className="menuitem-label">{item.label}</span>
          <Icon className={sidebarTriggerIconClassName} name="arrow-right" />
        </button>
      </Tippy>
      <SidebarPanel isVisible={isVisible} isOpen={isOpen} depth={depth}>
        <div className="sidebar-sub-menu-panel">
          <h2
            id={`wagtail-sidebar-submenu${path.split('.').join('-')}-title`}
            className={`${item.classNames} w-h4`}
          >
            {item.iconName && (
              <Icon name={item.iconName} className="icon--submenu-header" />
            )}
            {item.label}
          </h2>
          <ul
            aria-labelledby={`wagtail-sidebar-submenu${path
              .split('.')
              .join('-')}-title`}
          >
            {renderMenu(path, item.menuItems, slim, state, dispatch, navigate)}
          </ul>
          {item.footerText && (
            <p className="sidebar-sub-menu-panel__footer">{item.footerText}</p>
          )}
        </div>
      </SidebarPanel>
    </li>
  );
};

export class SubMenuItemDefinition implements MenuItemDefinition {
  name: string;
  label: string;
  menuItems: MenuItemDefinition[];
  iconName: string | null;
  classNames?: string;
  footerText: string;

  constructor(
    {
      name,
      label,
      icon_name: iconName = null,
      classnames = undefined,
      footer_text: footerText = '',
    }: any,
    menuItems: MenuItemDefinition[],
  ) {
    this.name = name;
    this.label = label;
    this.menuItems = menuItems;
    this.iconName = iconName;
    this.classNames = classnames;
    this.footerText = footerText;
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
