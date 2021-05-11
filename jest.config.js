// See https://jestjs.io/docs/en/configuration.
module.exports = {
    moduleNameMapper: {
        'jquery': '<rootDir>/wagtail/admin/static_src/wagtailadmin/js/vendor/jquery-3.5.1.min.js'
    },
    moduleFileExtensions: ['js', 'ts', 'tsx', 'json', 'node'],
    transform: {
        '^.+\\.(js|ts|tsx)$': 'ts-jest',
        '^.+\\.mdx?$': '@storybook/addon-docs/jest-transform-mdx',
    },
    collectCoverageFrom: ['src/**/*.{js,ts,tsx}', '!<rootDir>/node_modules/'],
    testPathIgnorePatterns: ['/node_modules/', '/smoke/', '/build/'],
    coveragePathIgnorePatterns: ['/node_modules/', '/tests/', '<rootDir>/client/tests', '.stories.{js,ts,tsx}'],
    setupFilesAfterEnv: ['<rootDir>/client/tests/setupTests.ts', '<rootDir>/client/tests/adapter.js', '<rootDir>/client/tests/stubs.js', '<rootDir>/client/tests/mock-fetch.js', '<rootDir>/client/tests/mock-jquery.js'],
    snapshotSerializers: ['enzyme-to-json/serializer'],
    globals: {
        APP_URL_PRODUCTION: 'http://localhost/',
        APP_URL_DEVELOPMENT: 'http://localhost/',
        APP_URL_DEPLOY: 'http://localhost/',
    },
};
