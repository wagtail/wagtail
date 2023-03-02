import type { Definition } from '@hotwired/stimulus';

// Order controller imports alphabetically.
import { ActionController } from './ActionController';
import { CountController } from './CountController';
import { MessagesController } from './MessagesController';
import { ProgressController } from './ProgressController';
import { SkipLinkController } from './SkipLinkController';
import { SlugController } from './SlugController';
import { SubmitController } from './SubmitController';
import { UpgradeController } from './UpgradeController';

/**
 * Important: Only add default core controllers that should load with the base admin JS bundle.
 */
export const coreControllerDefinitions: Definition[] = [
  // Keep this list in alphabetical order
  { controllerConstructor: ActionController, identifier: 'w-action' },
  { controllerConstructor: CountController, identifier: 'w-count' },
  { controllerConstructor: MessagesController, identifier: 'w-messages' },
  { controllerConstructor: ProgressController, identifier: 'w-progress' },
  { controllerConstructor: SkipLinkController, identifier: 'w-skip-link' },
  { controllerConstructor: SlugController, identifier: 'w-slug' },
  { controllerConstructor: SubmitController, identifier: 'w-submit' },
  { controllerConstructor: UpgradeController, identifier: 'w-upgrade' },
];
