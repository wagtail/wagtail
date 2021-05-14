import { ReactNode } from 'react';

export {};

// Declare globals provided by Django's JavaScript Catalog
// For more information, see: https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#module-django.views.i18n
declare global {
    interface Window {
        __REDUX_DEVTOOLS_EXTENSION__: any;
        registerShellView(name: string, render: (data: any, csrfToken: string) => ReactNode): void;
        csrfToken: string;
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
    }

    const wagtailConfig: WagtailConfig;
}
