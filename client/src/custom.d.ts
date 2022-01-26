export {};

declare global {
    interface Window {
        __REDUX_DEVTOOLS_EXTENSION__: any;
        telepath: any;
    }

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
            /* eslint-disable-next-line camelcase */
            display_name: string;
        }[];
        STRINGS: any;
    }
    const wagtailConfig: WagtailConfig;
}
