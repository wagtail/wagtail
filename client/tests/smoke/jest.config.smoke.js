// See https://jestjs.io/docs/en/configuration.
module.exports = {
    moduleNameMapper: {
        '^.+\\.(css|scss)$': '<rootDir>/../mocks/fileMock.js',
        '.*\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$':
            '<rootDir>/../mocks/fileMock.js',
        'jquery': '<rootDir>/../../../wagtail/admin/static_src/wagtailadmin/js/vendor/jquery-3.5.1.min.js'
    },
    moduleFileExtensions: ['js', 'ts', 'tsx', 'json', 'node'],
    transform: {
        '^.+\\.(js|ts|tsx)$': 'ts-jest',
        // '^.+\\.(css|scss)$': 'jest-transform-css',
        '^.+\\.mdx?$': '@storybook/addon-docs/jest-transform-mdx',
    },
    transformIgnorePatterns: [
        '<rootDir>/../../../node_modules/(?!@dump247).+(ts|tsx|js|jsx)$',
    ],
    setupFilesAfterEnv: ['<rootDir>/../setupTests.ts', '<rootDir>/../adapter.js', '<rootDir>/../stubs.js', '<rootDir>/../mock-fetch.js', '<rootDir>/../mock-jquery.js'],
    globals: {
        APP_URL_PRODUCTION: 'http://localhost/',
        APP_URL_DEVELOPMENT: 'http://localhost/',
        APP_URL_DEPLOY: 'http://localhost/',
    },
};
