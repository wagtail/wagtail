export {};

declare global {
  interface Window {
    __REDUX_DEVTOOLS_EXTENSION__: any;
    telepath: any;
  }

  // Get text

  // Wagtail globals

  interface WagtailConfig {
    ADMIN_API: {
      PAGES: string;
      DOCUMENTS: string;
      IMAGES: string;
      EXTRA_CHILDREN_PARAMETERS: string;
    };

    ADMIN_URLS: {
      PAGES: string;
    };

    I18N_ENABLED: boolean;
    LOCALES: {
      code: string;

      display_name: string;
    }[];
  }
  const wagtailConfig: WagtailConfig;
}
