/**
 * Compares the `package.json` dev dependencies against the `.pre-commit-config.yaml`.
 * Validating that any pre commit hook dependencies are in sync with the project packages.
 */

import fs from 'node:fs';
import { parse } from 'yaml';

import packageJson from '../package.json' with { type: 'json' };

const PRE_COMMIT_PATH = '.pre-commit-config.yaml';

const preCommitConfig = parse(fs.readFileSync(PRE_COMMIT_PATH, 'utf8'));
const { devDependencies } = packageJson;

// eslint-disable-next-line no-console
console.info(
  'Checking package dependencies against `.pre-commit-config.yaml`.',
);

const results = preCommitConfig.repos
  .flatMap(({ hooks }) =>
    hooks.flatMap(
      ({ id = '', additional_dependencies: additionalDependencies = [] }) => {
        if (!id || !additionalDependencies?.length) return [];

        return additionalDependencies
          .map((dependency) => {
            const version = dependency.split('@').at(-1);
            const [packageName] = dependency.split(`@${version}`, 1);
            return { version, packageName };
          })
          .map(
            ({
              isHook,
              version,
              packageName,
              matchedDependency = devDependencies[packageName],
            }) => ({
              isHook,
              version,
              packageName,
              matchedDependency,
              isValid: matchedDependency?.endsWith(version) || false,
            }),
          );
      },
    ),
  )
  .filter(({ isValid }) => !isValid);

if (results.length) {
  throw new Error(
    [
      `The following 'package.json' dependencies are not in sync with '${PRE_COMMIT_PATH}':`,
      ...results.map(
        ({ isHook, version, packageName, matchedDependency }) =>
          `${packageName}: ${version} (package.json: ${
            matchedDependency ?? 'N/A'
          })${isHook ? ' [hook]' : ''}`,
      ),
      '',
    ].join('\n'),
  );
}
