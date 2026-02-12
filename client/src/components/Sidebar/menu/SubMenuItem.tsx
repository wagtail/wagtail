import * as React from 'react';

import Tippy from '@tippyjs/react';
import Icon from '../../Icon/Icon';

import { isDismissed, renderMenu } from '../modules/MainMenu';
import { SidebarPanel } from '../SidebarPanel';
import { SIDEBAR_TRANSITION_DURATION } from '../Sidebar';
import { MenuItemDefinition, MenuItemProps } from './MenuItem';
import { gettext } from '../../../utils/gettext';
import SubMenuCloseButton from './SubMenuCloseButton';

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
  const [hasBeenOpened, setHasBeenOpened] = React.useState(false);

  const dismissibleCount = item.menuItems.filter(
    (subItem) => !isDismissed(subItem, state),
  ).length;

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
    // Only dispatch set-dismissible-state when there are dismissible items
    // in the submenu and the submenu has not been opened before. Note that
    // the term "submenu" for this component means that this menu item *has*
    // "sub" items (children), rather than the actual "sub" menu items inside it.
    if (!hasBeenOpened && dismissibleCount > 0) {
      // Dispatching set-dismissible-state from this submenu also collect
      // all dismissible items in the submenu and set their state to dismissed
      // on the server, so that those child items won't show up as "new" again on
      // the next load.
      // However, the client state for the child items is only updated on the
      // next reload or if the individual items are clicked, so that the user
      // has the chance to see the "new" badge for those items.
      // After clicking this at least once, even if hasBeenOpened is false on
      // the next load, all the child items have been dismissed (dismissibleCount == 0),
      // so the "new" badge will not show up again (unless the server adds a new item).
      dispatch({
        type: 'set-dismissible-state',
        item,
      });
    }

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
      setHasBeenOpened(true);
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
          {...item.attrs}
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

          {
            // Only show the dismissible badge if the menu item has not been
            // opened yet, so it's less distracting after the user has opened it.
          }
          {dismissibleCount > 0 && !hasBeenOpened && (
            <span className="w-dismissible-badge w-dismissible-badge--count">
              <span aria-hidden="true">{dismissibleCount}</span>
              <span className="w-sr-only">
                {dismissibleCount === 1
                  ? gettext('(1 new item in this menu)')
                  : gettext('(%(number)s new items in this menu)').replace(
                      '%(number)s',
                      `${dismissibleCount}`,
                    )}
              </span>
            </span>
          )}
          <Icon className={sidebarTriggerIconClassName} name="arrow-right" />
        </button>
      </Tippy>
      <SidebarPanel isVisible={isVisible} isOpen={isOpen} depth={depth}>
        <div className="sidebar-sub-menu-panel">
          <SubMenuCloseButton isVisible={isVisible} dispatch={dispatch} />
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
  attrs: { [key: string]: any };
  iconName: string | null;
  classNames?: string;
  footerText: string;

  constructor(
    {
      name,
      label,
      attrs = {},
      icon_name: iconName = null,
      classname = undefined,
      footer_text: footerText = '',
    }: any,
    menuItems: MenuItemDefinition[],
  ) {
    this.name = name;
    this.label = label;
    this.menuItems = menuItems;
    this.attrs = attrs;
    this.iconName = iconName;
    this.classNames = classname;
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
