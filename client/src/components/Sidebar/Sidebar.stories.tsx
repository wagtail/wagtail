import React from 'react';

import { Sidebar } from './Sidebar';
import { WagtailBrandingModuleDefinition } from './modules/WagtailBranding';
import { SearchModuleDefinition } from './modules/Search';
import { MainMenuModuleDefinition } from './modules/MainMenu';
import { PageExplorerMenuItemDefinition } from './menu/PageExplorerMenuItem';
import { LinkMenuItemDefinition } from './menu/LinkMenuItem';
import { SubMenuItemDefinition } from './menu/SubMenuItem';
import SVGIconSprite from '../SVGIconSprite';

export default { title: 'Sidebar/Sidebar', parameters: { layout: 'fullscreen' } };

export function sidebar() {
  const modules = [
    new WagtailBrandingModuleDefinition('/admin/', {
      mobileLogo: 'https://wagtail.io/static/wagtailadmin/images/wagtail-logo.svg',
      desktopLogoBody: 'https://wagtail.io/static/wagtailadmin/images/logo-body.svg',
      desktopLogoTail: 'https://wagtail.io/static/wagtailadmin/images/logo-tail.svg',
      desktopLogoEyeOpen: 'https://wagtail.io/static/wagtailadmin/images/logo-eyeopen.svg',
      desktopLogoEyeClosed: 'https://wagtail.io/static/wagtailadmin/images/logo-eyeclosed.svg'
    }),
    new SearchModuleDefinition('/admin/search/'),
    new MainMenuModuleDefinition(
      [
        new PageExplorerMenuItemDefinition({
          name: 'explorer',
          label: 'Pages',
          url: '/admin/pages',
          start_page_id: 1,
          icon_name: 'folder-open-inverse',
          classnames: '',
        }),
        new LinkMenuItemDefinition({
          name: 'images',
          label: 'Images',
          url: '/admin/images/',
          icon_name: 'image',
          classnames: '',
        }),
        new LinkMenuItemDefinition({
          name: 'documents',
          label: 'Documents',
          url: '/admin/documents/',
          icon_name: 'doc-full-inverse',
          classnames: '',
        }),
        new LinkMenuItemDefinition({
          name: 'snippets',
          label: 'Snippets',
          url: '/admin/snippets/',
          icon_name: 'snippet',
          classnames: '',
        }),
        new LinkMenuItemDefinition({
          name: 'forms',
          label: 'Forms',
          url: '/admin/forms/',
          icon_name: 'form',
          classnames: '',
        }),
        new SubMenuItemDefinition(
          {
            name: 'reports',
            label: 'Reports',
            icon_name: 'site',
            classnames: '',
          },
          [
            new LinkMenuItemDefinition({
              name: 'locked-pages',
              label: 'Locked Pages',
              url: '/admin/reports/locked/',
              icon_name: 'lock',
              classnames: '',
            }),
            new LinkMenuItemDefinition({
              name: 'workflows',
              label: 'Workflows',
              url: '/admin/reports/workflow/',
              icon_name: 'tasks',
              classnames: '',
            }),
            new LinkMenuItemDefinition({
              name: 'workflow-tasks',
              label: 'Workflow tasks',
              url: '/admin/reports/workflow_tasks/',
              icon_name: 'thumbtack',
              classnames: '',
            }),
            new LinkMenuItemDefinition({
              name: 'site-history',
              label: 'Site history',
              url: '/admin/reports/site-history/',
              icon_name: 'history',
              classnames: '',
            }),
          ]
        ),
        new SubMenuItemDefinition(
          {
            name: 'settings',
            label: 'Settings',
            icon_name: 'cogs',
            classnames: '',
          },
          [
            new LinkMenuItemDefinition({
              name: 'workflows',
              label: 'Workflows',
              url: '/admin/workflows/list/',
              icon_name: 'tasks',
              classnames: '',
            }),
            new LinkMenuItemDefinition({
              name: 'workflow-tasks',
              label: 'Workflow tasks',
              url: '/admin/workflows/tasks/index/',
              icon_name: 'thumbtack',
              classnames: '',
            }),
            new LinkMenuItemDefinition({
              name: 'users',
              label: 'Users',
              url: '/admin/users/',
              icon_name: 'user',
              classnames: '',
            }),
            new LinkMenuItemDefinition({
              name: 'groups',
              label: 'Groups',
              url: '/admin/groups/',
              icon_name: 'group',
              classnames: '',
            }),
            new LinkMenuItemDefinition({
              name: 'sites',
              label: 'Sites',
              url: '/admin/sites/',
              icon_name: 'site',
              classnames: '',
            }),
            new LinkMenuItemDefinition({
              name: 'collections',
              label: 'Collections',
              url: '/admin/collections/',
              icon_name: 'folder-open-1',
              classnames: '',
            }),
            new LinkMenuItemDefinition({
              name: 'redirects',
              label: 'Redirects',
              url: '/admin/redirects/',
              icon_name: 'redirect',
              classnames: '',
            }),
          ]
        ),
      ],
      [
        new LinkMenuItemDefinition({
          name: 'account',
          label: 'Account',
          url: '/admin/account/',
          icon_name: 'user',
          classnames: '',
        }),
        new LinkMenuItemDefinition({
          name: 'logout',
          label: 'Logout',
          url: '/admin/logout/',
          icon_name: 'logout',
          classnames: '',
        }),
      ],
      {
        name: 'Admin',
        avatarUrl: 'https://gravatar.com/avatar/e31ec811942afbf7b9ce0ac5affe426f?s=200&d=robohash&r=x',
      }
    )
  ];

  // Simulate navigation
  const [currentPath, setCurrentPath] = React.useState('/admin/');

  const navigate = (url: string) => {
    setCurrentPath(url);

    // Return resolved promise to close menu immediately
    return Promise.resolve();
  };

  // Add ready class to body to enable CSS transitions
  document.body.classList.add('ready');

  return (
    <div className="wrapper">
      <SVGIconSprite />
      <Sidebar modules={modules} currentPath={currentPath} navigate={navigate} />
      <main id="main" className="content-wrapper" role="main">
        <div className="content">
          <b>Current path:</b> {currentPath}
        </div>
      </main>
    </div>
  );
}
