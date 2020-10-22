export {};

declare global {
    interface Window { __REDUX_DEVTOOLS_EXTENSION__: any; }

    interface WagtailConfig {
        I18N_ENABLED: boolean;
        LOCALES: {
            code: string;
            /* eslint-disable-next-line camelcase */
            display_name: string;
        }[];
    }
    const wagtailConfig: WagtailConfig;
}
