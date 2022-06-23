import * as React from 'react';

import { Provider } from 'react-redux';
import Tippy from '@tippyjs/react';
import Icon from '../../Icon/Icon';
import { MenuItemProps } from './MenuItem';
import { LinkMenuItemDefinition } from './LinkMenuItem';
import PageExplorer, { initPageExplorerStore } from '../../PageExplorer';
import {
  openPageExplorer,
  closePageExplorer,
} from '../../PageExplorer/actions';
import { SidebarPanel } from '../SidebarPanel';
import { SIDEBAR_TRANSITION_DURATION } from '../Sidebar';

export const PageExplorerMenuItem: React.FunctionComponent<
  MenuItemProps<PageExplorerMenuItemDefinition>
> = ({ path, slim, item, state, dispatch, navigate }) => {
  const isOpen = state.navigationPath.startsWith(path);
  const isActive = isOpen || state.activePath.startsWith(path);
  const depth = path.split('.').length;
  const isInSubMenu = path.split('.').length > 2;
  const [isVisible, setIsVisible] = React.useState(false);

  const store = React.useRef<any>(null);
  if (!store.current) {
    store.current = initPageExplorerStore();
  }

  const onCloseExplorer = () => {
    // When a submenu is closed, we have to wait for the close animation
    // to finish before making it invisible
    setTimeout(() => {
      setIsVisible(false);
      if (store.current) {
        store.current.dispatch(closePageExplorer());
      }
    }, SIDEBAR_TRANSITION_DURATION);
  };

  React.useEffect(() => {
    if (isOpen) {
      // isOpen is set at the moment the user clicks the menu item
      setIsVisible(true);

      if (store.current) {
        store.current.dispatch(openPageExplorer(item.startPageId));
      }
    } else if (!isOpen && isVisible) {
      onCloseExplorer();
    }
  }, [isOpen]);

  const onClick = () => {
    // Open/close explorer
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
  };

  const className =
    'sidebar-menu-item sidebar-page-explorer-item' +
    (isActive ? ' sidebar-menu-item--active' : '') +
    (isInSubMenu ? ' sidebar-menu-item--in-sub-menu' : '');

  const sidebarTriggerIconClassName =
    'sidebar-sub-menu-trigger-icon' +
    (isOpen ? ' sidebar-sub-menu-trigger-icon--open' : '');

  return (
    <li className={className}>
      <Tippy disabled={isOpen || !slim} content={item.label} placement="right">
        <button
          onClick={onClick}
          className="sidebar-menu-item__link"
          aria-haspopup="dialog"
          aria-expanded={isOpen ? 'true' : 'false'}
          type="button"
        >
          <Icon name="folder-open-inverse" className="icon--menuitem" />
          <span className="menuitem-label">{item.label}</span>
          <Icon className={sidebarTriggerIconClassName} name="arrow-right" />
        </button>
      </Tippy>
      <div>
        <SidebarPanel
          isVisible={isVisible}
          isOpen={isOpen}
          depth={depth}
          widthPx={485}
        >
          {store.current && (
            <Provider store={store.current}>
              <PageExplorer
                isVisible={isVisible}
                navigate={navigate}
                onClose={onCloseExplorer}
              />
            </Provider>
          )}
        </SidebarPanel>
      </div>
    </li>
  );
};

export class PageExplorerMenuItemDefinition extends LinkMenuItemDefinition {
  startPageId: number;

  constructor(
    { name, label, url, icon_name: iconName = null, classnames = undefined },
    startPageId: number,
  ) {
    super({ name, label, url, icon_name: iconName, classnames });
    this.startPageId = startPageId;
  }

  render({ path, slim, state, dispatch, navigate }) {
    return (
      <PageExplorerMenuItem
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
