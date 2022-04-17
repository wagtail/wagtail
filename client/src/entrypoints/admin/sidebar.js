import { initSidebar } from '../../sidebar/components/Sidebar';
import { LinkMenuItemDefinition } from '../../sidebar/components/Sidebar/menu/LinkMenuItem';
import { SubMenuItemDefinition } from '../../sidebar/components/Sidebar/menu/SubMenuItem';
import { PageExplorerMenuItemDefinition } from '../../sidebar/components/Sidebar/menu/PageExplorerMenuItem';

import { WagtailBrandingModuleDefinition } from '../../sidebar/components/Sidebar/modules/WagtailBranding';
import { SearchModuleDefinition } from '../../sidebar/components/Sidebar/modules/Search';
import { MainMenuModuleDefinition } from '../../sidebar/components/Sidebar/modules/MainMenu';

window.telepath.register(
  'wagtail.sidebar.LinkMenuItem',
  LinkMenuItemDefinition,
);
window.telepath.register('wagtail.sidebar.SubMenuItem', SubMenuItemDefinition);
window.telepath.register(
  'wagtail.sidebar.PageExplorerMenuItem',
  PageExplorerMenuItemDefinition,
);

window.telepath.register(
  'wagtail.sidebar.WagtailBrandingModule',
  WagtailBrandingModuleDefinition,
);
window.telepath.register(
  'wagtail.sidebar.SearchModule',
  SearchModuleDefinition,
);
window.telepath.register(
  'wagtail.sidebar.MainMenuModule',
  MainMenuModuleDefinition,
);

document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
});
