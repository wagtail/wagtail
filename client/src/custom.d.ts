// Allows SVG files to be imported and used in TypeScript
declare module '*.svg' {
    const content: any;
    export default content;
}

// Declare globals provided by Django's JavaScript Catalog
// For more information, see: https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#module-django.views.i18n
declare module 'gettext' {
    // https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#gettext
    export default function gettext(text: string): string;

    // https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#ngettext
    export default function ngettext(singular: string, plural: string, count: number): string;

    // https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#interpolate
    // FIXME export default function interpolate(...): string;

    // https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#get-format
    type FormatType =
        'DATE_FORMAT' |
        'DATE_INPUT_FORMATS' |
        'DATETIME_FORMAT' |
        'DATETIME_INPUT_FORMATS' |
        'DECIMAL_SEPARATOR' |
        'FIRST_DAY_OF_WEEK' |
        'MONTH_DAY_FORMAT' |
        'NUMBER_GROUPING' |
        'SHORT_DATE_FORMAT' |
        'SHORT_DATETIME_FORMAT' |
        'THOUSAND_SEPARATOR' |
        'TIME_FORMAT' |
        'TIME_INPUT_FORMATS' |
        'YEAR_MONTH_FORMAT';
    export default function get_format(formatType: FormatType): string;

    // https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#gettext_noop
    export default function gettext_noop(text: string): string;

    // https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#pgettext
    export default function pgettext(context: string, text: string): string;

    // https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#npgettext
    export default function pgettext(context: string, text: string, count: number): string;

    // https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#pluralidx
    export default function pluralidx(count: number): boolean;
}
