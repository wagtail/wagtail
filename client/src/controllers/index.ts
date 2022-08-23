import type { Definition } from '@hotwired/stimulus';

import { AutoFieldController } from './AutoFieldController';

/**
 * Important: Only add default core controllers that should load with the base admin JS bundle.
 */
export const coreControllerDefinitions: Definition[] = [
  { controllerConstructor: AutoFieldController, identifier: 'w-auto-field' },
];
