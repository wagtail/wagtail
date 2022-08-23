/**
 * Any files in the format some-controller.ts within this folder will be prepared
 * as a definition array for Stimulus.
 *
 * The controller's name will be used to generate the Controller's identifier
 * e.g. `UpgradeController` -> `w-upgrade`
 * e.g. `SomeOtherSuperController` -> `w-some-other-super`
 */

import type { Definition } from '@hotwired/stimulus';

import type { AbstractControllerConstructor } from './AbstractController';
import { kebabCase } from '../utils/text';

interface DefinitionWithAbstractController extends Definition {
  controllerConstructor: AbstractControllerConstructor;
}

const context = require.context('./', false, /[A-Za-z]*Controller\.ts$/);

interface ECMAScriptModule {
  __esModule: boolean;
  default?: AbstractControllerConstructor;
}

/**
 * Return the default module, if exported, otherwise find the first function
 * (remember classes are functions) that exist as a named export.
 */
const getConstructor = (
  module: ECMAScriptModule,
): AbstractControllerConstructor =>
  module.default ||
  Object.values(module).find((value) => typeof value === 'function');

/**
 * Convert a Stimulus Controller class' name to a consistently formatted Stimulus
 * identifier with the prefix `w-`.
 *
 * @example
 * getIdentifier('VeryHelpfulController');
 * // outputs -> 'w-very-helpful
 */
const getIdentifier = (key: string) =>
  kebabCase((key.match(/^(?:\.\/)?(\w+)(?:Controller)\..+?$/) || [])[1], {
    prefix: 'w',
  });

/**
 * Parses the imported context to output an array of controller / identifier definitions.
 * Prepares the identifier based on the file name (remember classes may be renamed by
 * minifier).
 */
export const controllerDefinitions: DefinitionWithAbstractController[] = context
  .keys()
  .map((key) => {
    const controllerConstructor = getConstructor(context(key)) || null;
    return {
      controllerConstructor,
      identifier: getIdentifier(key),
    };
  })
  .filter(
    (item): item is DefinitionWithAbstractController =>
      item?.controllerConstructor?.isIncludedInCore && !!item?.identifier,
  );
