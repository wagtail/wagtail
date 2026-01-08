import type { CommentApp } from './components/CommentApp/main';

export interface WagtailConfig {
  /** For editing models that can be translated, the target locale's language code will be provided. */
  ACTIVE_CONTENT_LOCALE?: string;
  ADMIN_API: {
    PAGES: string;
    DOCUMENTS: string;
    IMAGES: string;
    EXTRA_CHILDREN_PARAMETERS: string;
  };
  ADMIN_URLS: {
    DISMISSIBLES: string;
    PAGES: string;
    BLOCK_PREVIEW: string;
  };
  CSRF_HEADER_NAME: string;
  CSRF_TOKEN: string;
  I18N_ENABLED: boolean;
  LOCALES: {
    code: string;
    display_name: string;
  }[];
  KEYBOARD_SHORTCUTS_ENABLED: boolean;
}

declare global {
  interface Window {
    __REDUX_DEVTOOLS_EXTENSION__: any;
    telepath: any;
    comments?: { commentApp: CommentApp };
  }

  const wagtailConfig: WagtailConfig;
}
