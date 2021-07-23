import * as React from 'react';
import ReactDOM from 'react-dom';
import Cookies from 'js-cookie';

import { Sidebar } from './Sidebar';

export const SIDEBAR_COLLAPSED_COOKIE_NAME = 'wagtail_sidebar_collapsed';

export function initSidebar() {
  const element = document.getElementById('wagtail-sidebar');

  const navigate = (url: string) => {
    window.location.href = url;

    // Return a promise that never resolves.
    // This promise is used to indicate to any open submenus that the next page has loaded and it should close.
    // As all navigation from the menu at the moment takes the user to another page, we don't need to close the menus.
    // We will need to update this if we later add the ability to render views on the client side.
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    return new Promise<void>(() => {});
  };

  if (element instanceof HTMLElement && element.dataset.props) {
    const props = window.telepath.unpack(JSON.parse(element.dataset.props));

    const collapsedCookie: any = Cookies.get(SIDEBAR_COLLAPSED_COOKIE_NAME);
    // Cast to boolean
    const collapsed = !((collapsedCookie === undefined || collapsedCookie === '0'));

    const onExpandCollapse = (_collapsed: boolean) => {
      if (_collapsed) {
        document.body.classList.add('sidebar-collapsed');
        Cookies.set(SIDEBAR_COLLAPSED_COOKIE_NAME, 1);
      } else {
        document.body.classList.remove('sidebar-collapsed');
        Cookies.set(SIDEBAR_COLLAPSED_COOKIE_NAME, 0);
      }
    };

    ReactDOM.render(
      <Sidebar
        modules={props.modules}
        strings={wagtailConfig.STRINGS}
        collapsedOnLoad={collapsed}
        currentPath={window.location.pathname}
        navigate={navigate}
        onExpandCollapse={onExpandCollapse}
      />,
      element,
      () => {
        document.body.classList.add('ready');
      }
    );
  }
}
