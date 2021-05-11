// See https://jestjs.io/docs/en/configuration.
module.exports = {
    moduleNameMapper: {},
    moduleFileExtensions: ['js', 'ts', 'tsx', 'json', 'node'],
    transform: {
        '^.+\\.(js|ts|tsx)$': 'ts-jest',
        '^.+\\.mdx?$': '@storybook/addon-docs/jest-transform-mdx',
    },
    collectCoverageFrom: ['src/**/*.{js,ts,tsx}', '!<rootDir>/node_modules/'],
    testPathIgnorePatterns: ['/node_modules/', '/smoke/'],
    coveragePathIgnorePatterns: ['<rootDir>/client/tests', '.stories.{js,ts,tsx}'],
    setupFilesAfterEnv: ['<rootDir>/client/tests/setupTests.ts'],
    globals: {
        APP_URL_PRODUCTION: 'http://localhost/',
        APP_URL_DEVELOPMENT: 'http://localhost/',
        APP_URL_DEPLOY: 'http://localhost/',
    },
};
