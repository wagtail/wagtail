import type { Definition } from '@hotwired/stimulus';

// Order controller imports alphabetically.
import { ActionController } from './ActionController';
import { ProgressController } from './ProgressController';
import { SkipLinkController } from './SkipLinkController';
import { SubmitController } from './SubmitController';
import { UpgradeController } from './UpgradeController';

/**
 * Important: Only add default core controllers that should load with the base admin JS bundle.
 */
export const coreControllerDefinitions: Definition[] = [
  // Keep this list in alphabetical order
  { controllerConstructor: ActionController, identifier: 'w-action' },
  { controllerConstructor: ProgressController, identifier: 'w-progress' },
  { controllerConstructor: SkipLinkController, identifier: 'w-skip-link' },
  { controllerConstructor: SubmitController, identifier: 'w-submit' },
  { controllerConstructor: UpgradeController, identifier: 'w-upgrade' },
];
