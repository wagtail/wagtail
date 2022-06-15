import * as React from 'react';

import { ModuleDefinition, Sidebar } from './Sidebar';
import { SearchModuleDefinition } from './modules/Search';
import { MainMenuModuleDefinition } from './modules/MainMenu';
import { PageExplorerMenuItemDefinition } from './menu/PageExplorerMenuItem';
import { LinkMenuItemDefinition } from './menu/LinkMenuItem';
import { SubMenuItemDefinition } from './menu/SubMenuItem';
import { WagtailBrandingModuleDefinition } from './modules/WagtailBranding';

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
          classnames: '',
        },
        1,
      ),
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
        ],
      ),
      new SubMenuItemDefinition(
        {
          name: 'settings',
          label: 'Settings',
          icon_name: 'cogs',
          classnames: '',
          footer_text: 'Wagtail Version',
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
        ],
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
        label: 'Log out',
        url: '/admin/logout/',
        icon_name: 'logout',
        classnames: '',
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

  // Add ready class to body to enable CSS transitions
  document.body.classList.add('ready');

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
        classnames: '',
      },
      [
        new LinkMenuItemDefinition({
          name: 'item',
          label: 'Item',
          url: '/admin/item/',
          icon_name: 'user',
          classnames: '',
        }),
        new SubMenuItemDefinition(
          {
            name: 'nested-menu',
            label: 'Nested menu',
            icon_name: 'folder-open-1',
            classnames: '',
          },
          [
            new LinkMenuItemDefinition({
              name: 'item',
              label: 'Item',
              url: '/admin/item/item/',
              icon_name: 'user',
              classnames: '',
            }),
            new SubMenuItemDefinition(
              {
                name: 'deeply-nested-menu',
                label: 'Deeply nested menu',
                icon_name: 'side',
                classnames: '',
              },
              [
                new LinkMenuItemDefinition({
                  name: 'item',
                  label: 'Item',
                  url: '/admin/item/item/item/',
                  icon_name: 'user',
                  classnames: '',
                }),
              ],
            ),
            new SubMenuItemDefinition(
              {
                name: 'another-deeply-nested-menu',
                label: 'Another deeply nested menu',
                icon_name: 'user',
                classnames: '',
              },
              [
                new LinkMenuItemDefinition({
                  name: 'item',
                  label: 'Item',
                  url: '/admin/item/item/item2/',
                  icon_name: 'user',
                  classnames: '',
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

  const menuItems = [];
  for (let i = 0; i < 100; i++) {
    menuItems.push(
      new LinkMenuItemDefinition({
        name: `item-${i}`,
        label: `Item ${i}`,
        url: `/admin/item-${i}/`,
        icon_name: 'snippet',
        classnames: '',
      }),
    );
  }

  menuModule.menuItems.push(
    new SubMenuItemDefinition(
      {
        name: 'large-menu',
        label: 'Large menu',
        icon_name: 'cogs',
        classnames: '',
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
      new PageExplorerMenuItemDefinition({
        name: 'explorer',
        label: 'صفحات',
        url: '/admin/pages',
        start_page_id: 1,
        icon_name: 'folder-open-inverse',
        classnames: '',
      }),
      new LinkMenuItemDefinition({
        name: 'images',
        label: 'صور',
        url: '/admin/images/',
        icon_name: 'image',
        classnames: '',
      }),
      new LinkMenuItemDefinition({
        name: 'documents',
        label: 'وثائق',
        url: '/admin/documents/',
        icon_name: 'doc-full-inverse',
        classnames: '',
      }),
      new LinkMenuItemDefinition({
        name: 'snippets',
        label: 'قصاصات',
        url: '/admin/snippets/',
        icon_name: 'snippet',
        classnames: '',
      }),
      new LinkMenuItemDefinition({
        name: 'forms',
        label: 'نماذج',
        url: '/admin/forms/',
        icon_name: 'form',
        classnames: '',
      }),
      new SubMenuItemDefinition(
        {
          name: 'reports',
          label: 'التقارير',
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
        ],
      ),
      new SubMenuItemDefinition(
        {
          name: 'settings',
          label: 'إعدادات',
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
            label: 'مستخدمين',
            url: '/admin/users/',
            icon_name: 'user',
            classnames: '',
          }),
          new LinkMenuItemDefinition({
            name: 'groups',
            label: 'مجموعات',
            url: '/admin/groups/',
            icon_name: 'group',
            classnames: '',
          }),
          new LinkMenuItemDefinition({
            name: 'sites',
            label: 'مواقع',
            url: '/admin/sites/',
            icon_name: 'site',
            classnames: '',
          }),
          new LinkMenuItemDefinition({
            name: 'collections',
            label: 'مجموعات',
            url: '/admin/collections/',
            icon_name: 'folder-open-1',
            classnames: '',
          }),
          new LinkMenuItemDefinition({
            name: 'redirects',
            label: 'اعادة التوجيهات',
            url: '/admin/redirects/',
            icon_name: 'redirect',
            classnames: '',
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
        classnames: '',
      }),
      new LinkMenuItemDefinition({
        name: 'logout',
        label: 'تسجيل الخروج',
        url: '/admin/logout/',
        icon_name: 'logout',
        classnames: '',
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
