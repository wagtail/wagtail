import type { Definition } from '@hotwired/stimulus';

// Order controller imports alphabetically.
import { ActionController } from './ActionController';
import { AutoFieldController } from './AutoFieldController';
import { SkipLinkController } from './SkipLinkController';
import { UpgradeController } from './UpgradeController';

/**
 * Important: Only add default core controllers that should load with the base admin JS bundle.
 */
export const coreControllerDefinitions: Definition[] = [
  // Keep this list alphabetized.
  { controllerConstructor: ActionController, identifier: 'w-action' },
  { controllerConstructor: AutoFieldController, identifier: 'w-auto-field' },
  { controllerConstructor: SkipLinkController, identifier: 'w-skip-link' },
  { controllerConstructor: UpgradeController, identifier: 'w-upgrade' },
];
