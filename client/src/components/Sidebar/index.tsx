import * as React from 'react';
import ReactDOM from 'react-dom';
import Cookies from 'js-cookie';

import { Sidebar } from './Sidebar';
import { noop } from '../../utils/noop';

export const SIDEBAR_COLLAPSED_COOKIE_NAME = 'wagtail_sidebar_collapsed';

export function initSidebar() {
  const cookieOptions = { sameSite: 'lax' };
  const element = document.getElementById('wagtail-sidebar');
  const rawProps = document.getElementById('wagtail-sidebar-props');

  const navigate = (url: string) => {
    window.location.href = url;

    // Return a promise that never resolves.
    // This promise is used to indicate to any open submenus that the next page has loaded and it should close.
    // As all navigation from the menu at the moment takes the user to another page, we don't need to close the menus.
    // We will need to update this if we later add the ability to render views on the client side.
    return new Promise<void>(noop);
  };

  if (element && rawProps?.textContent) {
    const props = window.telepath.unpack(JSON.parse(rawProps.textContent));

    const collapsedCookie: any = Cookies.get(SIDEBAR_COLLAPSED_COOKIE_NAME);
    // Cast to boolean
    const collapsed = !(
      collapsedCookie === undefined || collapsedCookie === '0'
    );

    const onExpandCollapse = (_collapsed: boolean) => {
      if (_collapsed) {
        document.body.classList.add('sidebar-collapsed');
        Cookies.set(SIDEBAR_COLLAPSED_COOKIE_NAME, 1, cookieOptions);
      } else {
        document.body.classList.remove('sidebar-collapsed');
        Cookies.set(SIDEBAR_COLLAPSED_COOKIE_NAME, 0, cookieOptions);
      }
    };

    ReactDOM.render(
      <Sidebar
        modules={props.modules}
        collapsedOnLoad={collapsed}
        currentPath={window.location.pathname}
        navigate={navigate}
        onExpandCollapse={onExpandCollapse}
      />,
      element,
      () => {
        document.body.classList.add('ready');
        document
          .querySelector('[data-wagtail-sidebar]')
          ?.classList.remove('sidebar-loading');
      },
    );
  }
}
