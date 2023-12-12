import * as React from 'react';

import { ModuleDefinition, Sidebar } from './Sidebar';
import { SearchModuleDefinition } from './modules/Search';
import { MainMenuModuleDefinition } from './modules/MainMenu';
import { PageExplorerMenuItemDefinition } from './menu/PageExplorerMenuItem';
import { LinkMenuItemDefinition } from './menu/LinkMenuItem';
import { SubMenuItemDefinition } from './menu/SubMenuItem';
import { WagtailBrandingModuleDefinition } from './modules/WagtailBranding';
import { range } from '../../utils/range';
import { MenuItemDefinition } from './menu/MenuItem';

export default {
  title: 'Sidebar/Sidebar',
  parameters: { layout: 'fullscreen' },
};

function searchModule(): SearchModuleDefinition {
  return new SearchModuleDefinition('/admin/search/');
}

function bogStandardMenuModule(): MainMenuModuleDefinition {
  return new MainMenuModuleDefinition(
    [
      new PageExplorerMenuItemDefinition(
        {
          name: 'explorer',
          label: 'Pages',
          url: '/admin/pages',
          icon_name: 'folder-open-inverse',
          classname: '',
        },
        1,
      ),
      new LinkMenuItemDefinition({
        name: 'images',
        label: 'Images',
        url: '/admin/images/',
        icon_name: 'image',
        classname: '',
      }),
      new LinkMenuItemDefinition({
        name: 'documents',
        label: 'Documents',
        url: '/admin/documents/',
        icon_name: 'doc-full-inverse',
        classname: '',
      }),
      new LinkMenuItemDefinition({
        name: 'snippets',
        label: 'Snippets',
        url: '/admin/snippets/',
        icon_name: 'snippet',
        classname: '',
      }),
      new LinkMenuItemDefinition({
        name: 'forms',
        label: 'Forms',
        url: '/admin/forms/',
        icon_name: 'form',
        classname: '',
      }),
      new SubMenuItemDefinition(
        {
          name: 'reports',
          label: 'Reports',
          icon_name: 'site',
          classname: '',
        },
        [
          new LinkMenuItemDefinition({
            name: 'locked-pages',
            label: 'Locked pages',
            url: '/admin/reports/locked/',
            icon_name: 'lock',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'workflows',
            label: 'Workflows',
            url: '/admin/reports/workflow/',
            icon_name: 'tasks',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'workflow-tasks',
            label: 'Workflow tasks',
            url: '/admin/reports/workflow_tasks/',
            icon_name: 'thumbtack',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'site-history',
            label: 'Site history',
            url: '/admin/reports/site-history/',
            icon_name: 'history',
            classname: '',
          }),
        ],
      ),
      new SubMenuItemDefinition(
        {
          name: 'settings',
          label: 'Settings',
          icon_name: 'cogs',
          classname: '',
          footer_text: 'Wagtail Version',
        },
        [
          new LinkMenuItemDefinition({
            name: 'workflows',
            label: 'Workflows',
            url: '/admin/workflows/list/',
            icon_name: 'tasks',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'workflow-tasks',
            label: 'Workflow tasks',
            url: '/admin/workflows/tasks/index/',
            icon_name: 'thumbtack',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'users',
            label: 'Users',
            url: '/admin/users/',
            icon_name: 'user',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'groups',
            label: 'Groups',
            url: '/admin/groups/',
            icon_name: 'group',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'sites',
            label: 'Sites',
            url: '/admin/sites/',
            icon_name: 'site',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'collections',
            label: 'Collections',
            url: '/admin/collections/',
            icon_name: 'folder-open-1',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'redirects',
            label: 'Redirects',
            url: '/admin/redirects/',
            icon_name: 'redirect',
            classname: '',
          }),
        ],
      ),
    ],
    [
      new LinkMenuItemDefinition({
        name: 'account',
        label: 'Account',
        url: '/admin/account/',
        icon_name: 'user',
        classname: '',
      }),
      new LinkMenuItemDefinition({
        name: 'logout',
        label: 'Log out',
        url: '/admin/logout/',
        icon_name: 'logout',
        classname: '',
      }),
    ],
    {
      name: 'Admin',
      avatarUrl:
        'https://gravatar.com/avatar/e31ec811942afbf7b9ce0ac5affe426f?s=200&d=robohash&r=x',
    },
  );
}

interface RenderSidebarStoryOptions {
  rtl?: boolean;
}

function renderSidebarStory(
  modules: ModuleDefinition[],
  { rtl = false }: RenderSidebarStoryOptions = {},
) {
  // Add branding to all sidebar stories by default
  const wagtailBrandingModule = new WagtailBrandingModuleDefinition('');
  modules.unshift(wagtailBrandingModule);

  // Simulate navigation
  const [currentPath, setCurrentPath] = React.useState('/admin/');

  const navigate = (url: string) => {
    setCurrentPath(url);

    // Return resolved promise to close menu immediately
    return Promise.resolve();
  };

  const onExpandCollapse = (collapsed: boolean) => {
    if (collapsed) {
      document.body.classList.add('sidebar-collapsed');
    } else {
      document.body.classList.remove('sidebar-collapsed');
    }
  };

  if (rtl) {
    document.documentElement.setAttribute('dir', 'rtl');
  } else {
    document.documentElement.setAttribute('dir', 'ltr');
  }

  React.useEffect(
    () => () => {
      document.documentElement.removeAttribute('dir');
    },
    [],
  );

  return (
    <div className="wrapper">
      <Sidebar
        collapsedOnLoad={false}
        modules={modules}
        currentPath={currentPath}
        navigate={navigate}
        onExpandCollapse={onExpandCollapse}
      />
      <main id="main" className="content-wrapper">
        <div className="content">
          <b>Current path:</b> {currentPath}
        </div>
      </main>
    </div>
  );
}

export function standard() {
  return renderSidebarStory([searchModule(), bogStandardMenuModule()]);
}

export function withNestedSubmenu() {
  const menuModule = bogStandardMenuModule();

  menuModule.menuItems.push(
    new SubMenuItemDefinition(
      {
        name: 'nested-menu',
        label: 'Nested menu',
        icon_name: 'cogs',
        classname: '',
      },
      [
        new LinkMenuItemDefinition({
          name: 'item',
          label: 'Item',
          url: '/admin/item/',
          icon_name: 'user',
          classname: '',
        }),
        new SubMenuItemDefinition(
          {
            name: 'nested-menu',
            label: 'Nested menu',
            icon_name: 'folder-open-1',
            classname: '',
          },
          [
            new LinkMenuItemDefinition({
              name: 'item',
              label: 'Item',
              url: '/admin/item/item/',
              icon_name: 'user',
              classname: '',
            }),
            new SubMenuItemDefinition(
              {
                name: 'deeply-nested-menu',
                label: 'Deeply nested menu',
                icon_name: 'side',
                classname: '',
              },
              [
                new LinkMenuItemDefinition({
                  name: 'item',
                  label: 'Item',
                  url: '/admin/item/item/item/',
                  icon_name: 'user',
                  classname: '',
                }),
              ],
            ),
            new SubMenuItemDefinition(
              {
                name: 'another-deeply-nested-menu',
                label: 'Another deeply nested menu',
                icon_name: 'user',
                classname: '',
              },
              [
                new LinkMenuItemDefinition({
                  name: 'item',
                  label: 'Item',
                  url: '/admin/item/item/item2/',
                  icon_name: 'user',
                  classname: '',
                }),
              ],
            ),
          ],
        ),
      ],
    ),
  );

  return renderSidebarStory([searchModule(), menuModule]);
}

export function withLargeSubmenu() {
  const menuModule = bogStandardMenuModule();

  const menuItems: MenuItemDefinition[] = [];
  range(0, 100).forEach((i) => {
    menuItems.push(
      new LinkMenuItemDefinition({
        name: `item-${i}`,
        label: `Item ${i}`,
        url: `/admin/item-${i}/`,
        icon_name: 'snippet',
        classname: '',
      }),
    );
  });

  menuModule.menuItems.push(
    new SubMenuItemDefinition(
      {
        name: 'large-menu',
        label: 'Large menu',
        icon_name: 'cogs',
        classname: '',
        footer_text: 'Footer text',
      },
      menuItems,
    ),
  );

  return renderSidebarStory([searchModule(), menuModule]);
}

export function withoutSearch() {
  return renderSidebarStory([bogStandardMenuModule()]);
}

function arabicMenuModule(): MainMenuModuleDefinition {
  return new MainMenuModuleDefinition(
    [
      new PageExplorerMenuItemDefinition(
        {
          name: 'explorer',
          label: 'صفحات',
          url: '/admin/pages',
          icon_name: 'folder-open-inverse',
          classname: '',
        },
        1,
      ),
      new LinkMenuItemDefinition({
        name: 'images',
        label: 'صور',
        url: '/admin/images/',
        icon_name: 'image',
        classname: '',
      }),
      new LinkMenuItemDefinition({
        name: 'documents',
        label: 'وثائق',
        url: '/admin/documents/',
        icon_name: 'doc-full-inverse',
        classname: '',
      }),
      new LinkMenuItemDefinition({
        name: 'snippets',
        label: 'قصاصات',
        url: '/admin/snippets/',
        icon_name: 'snippet',
        classname: '',
      }),
      new LinkMenuItemDefinition({
        name: 'forms',
        label: 'نماذج',
        url: '/admin/forms/',
        icon_name: 'form',
        classname: '',
      }),
      new SubMenuItemDefinition(
        {
          name: 'reports',
          label: 'التقارير',
          icon_name: 'site',
          classname: '',
        },
        [
          new LinkMenuItemDefinition({
            name: 'locked-pages',
            label: 'Locked pages',
            url: '/admin/reports/locked/',
            icon_name: 'lock',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'workflows',
            label: 'Workflows',
            url: '/admin/reports/workflow/',
            icon_name: 'tasks',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'workflow-tasks',
            label: 'Workflow tasks',
            url: '/admin/reports/workflow_tasks/',
            icon_name: 'thumbtack',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'site-history',
            label: 'Site history',
            url: '/admin/reports/site-history/',
            icon_name: 'history',
            classname: '',
          }),
        ],
      ),
      new SubMenuItemDefinition(
        {
          name: 'settings',
          label: 'إعدادات',
          icon_name: 'cogs',
          classname: '',
        },
        [
          new LinkMenuItemDefinition({
            name: 'workflows',
            label: 'Workflows',
            url: '/admin/workflows/list/',
            icon_name: 'tasks',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'workflow-tasks',
            label: 'Workflow tasks',
            url: '/admin/workflows/tasks/index/',
            icon_name: 'thumbtack',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'users',
            label: 'مستخدمين',
            url: '/admin/users/',
            icon_name: 'user',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'groups',
            label: 'مجموعات',
            url: '/admin/groups/',
            icon_name: 'group',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'sites',
            label: 'مواقع',
            url: '/admin/sites/',
            icon_name: 'site',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'collections',
            label: 'مجموعات',
            url: '/admin/collections/',
            icon_name: 'folder-open-1',
            classname: '',
          }),
          new LinkMenuItemDefinition({
            name: 'redirects',
            label: 'اعادة التوجيهات',
            url: '/admin/redirects/',
            icon_name: 'redirect',
            classname: '',
          }),
        ],
      ),
    ],
    [
      new LinkMenuItemDefinition({
        name: 'account',
        label: 'حساب',
        url: '/admin/account/',
        icon_name: 'user',
        classname: '',
      }),
      new LinkMenuItemDefinition({
        name: 'logout',
        label: 'تسجيل الخروج',
        url: '/admin/logout/',
        icon_name: 'logout',
        classname: '',
      }),
    ],
    {
      name: 'Admin',
      avatarUrl:
        'https://gravatar.com/avatar/e31ec811942afbf7b9ce0ac5affe426f?s=200&d=robohash&r=x',
    },
  );
}

export function rightToLeft() {
  return renderSidebarStory([searchModule(), arabicMenuModule()], {
    rtl: true,
  });
}
