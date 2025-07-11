/**
 * Compares the `package.json` dev dependencies against the `.pre-commit-config.yaml`.
 * Validating that any pre commit hook dependencies are in sync with the project packages.
 */

import fs from 'node:fs';
import { parse } from 'yaml';

import packageJson from '../package.json' with { type: 'json' };

const PACKAGE_JSON = 'package.json';
const PRE_COMMIT_PATH = 'pre-commit-config.yaml';

const { devDependencies } = packageJson;
const { repos: preCommitRepos } = parse(
  fs.readFileSync('.' + PRE_COMMIT_PATH, 'utf8'),
);

// eslint-disable-next-line no-console
console.info(`Checking package dependencies against ${PRE_COMMIT_PATH}.`);

const errorMessages = [];

preCommitRepos.forEach(({ hooks }) => {
  hooks.forEach(({ id = '', additional_dependencies: dependencies = [] }) => {
    if (!id || !dependencies?.length) return;

    dependencies.forEach((dependency) => {
      const preCommitVersion = dependency.split('@').at(-1);
      const [packageName] = dependency.split(`@${preCommitVersion}`, 1);
      const packageVersion = devDependencies[packageName];
      if (packageVersion?.endsWith(preCommitVersion) || false) return;

      errorMessages.push(
        [
          ' →',
          `${PRE_COMMIT_PATH} [${packageName}: ${preCommitVersion}]`,
          `${PACKAGE_JSON}: [${packageName}: ${packageVersion ?? 'not found'}]`,
        ].join(' '),
      );
    });
  });
});

if (errorMessages.length) {
  throw new Error(
    [
      `The following '${PACKAGE_JSON}' dependencies are not in sync with '${PRE_COMMIT_PATH}':`,
      ...errorMessages,
      '',
    ].join('\n'),
  );
}
