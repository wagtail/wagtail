// See https://jestjs.io/docs/en/configuration.
module.exports = {
    moduleNameMapper: {
        '^.+\\.(css|scss)$': '<rootDir>/client/tests/mocks/fileMock.js',
        '.*\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$':
            '<rootDir>/client/tests/mocks/fileMock.js',
    },
    moduleFileExtensions: ['js', 'ts', 'tsx', 'json', 'node'],
    transform: {
        '^.+\\.(js|ts|tsx)$': 'ts-jest',
        // '^.+\\.(css|scss)$': 'jest-transform-css',
        '^.+\\.mdx?$': '@storybook/addon-docs/jest-transform-mdx',
    },
    globals: {
        APP_URL_PRODUCTION: 'http://localhost/',
        APP_URL_DEVELOPMENT: 'http://localhost/',
        APP_URL_DEPLOY: 'http://localhost/',
    },
};
