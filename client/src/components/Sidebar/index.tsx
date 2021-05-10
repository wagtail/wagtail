import * as React from 'react';
import ReactDOM from 'react-dom';

import { Sidebar } from './Sidebar';

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

    const onExpandCollapse = (collapsed: boolean) => {
      if (collapsed) {
        document.body.classList.add('sidebar-collapsed');
      } else {
        document.body.classList.remove('sidebar-collapsed');
      }
    };

    ReactDOM.render(
      <Sidebar
        modules={props.modules}
        strings={wagtailConfig.STRINGS}
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
