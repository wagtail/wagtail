import type { Definition } from '@hotwired/stimulus';

// Order controller imports alphabetically.
import { ActionController } from './ActionController';
import { AutosizeController } from './AutosizeController';
import { BulkController } from './BulkController';
import { CountController } from './CountController';
import { DismissibleController } from './DismissibleController';
import { DropdownController } from './DropdownController';
import { MessagesController } from './MessagesController';
import { ProgressController } from './ProgressController';
import { SkipLinkController } from './SkipLinkController';
import { SlugController } from './SlugController';
import { SubmitController } from './SubmitController';
import { SwapController } from './SwapController';
import { SyncController } from './SyncController';
import { TagController } from './TagController';
import { TooltipController } from './TooltipController';
import { UpgradeController } from './UpgradeController';

/**
 * Important: Only add default core controllers that should load with the base admin JS bundle.
 */
export const coreControllerDefinitions: Definition[] = [
  // Keep this list in alphabetical order
  { controllerConstructor: ActionController, identifier: 'w-action' },
  { controllerConstructor: AutosizeController, identifier: 'w-autosize' },
  { controllerConstructor: BulkController, identifier: 'w-bulk' },
  { controllerConstructor: CountController, identifier: 'w-count' },
  { controllerConstructor: DismissibleController, identifier: 'w-dismissible' },
  { controllerConstructor: DropdownController, identifier: 'w-dropdown' },
  { controllerConstructor: MessagesController, identifier: 'w-messages' },
  { controllerConstructor: ProgressController, identifier: 'w-progress' },
  { controllerConstructor: SkipLinkController, identifier: 'w-skip-link' },
  { controllerConstructor: SlugController, identifier: 'w-slug' },
  { controllerConstructor: SubmitController, identifier: 'w-submit' },
  { controllerConstructor: SwapController, identifier: 'w-swap' },
  { controllerConstructor: SyncController, identifier: 'w-sync' },
  { controllerConstructor: TagController, identifier: 'w-tag' },
  { controllerConstructor: TooltipController, identifier: 'w-tooltip' },
  { controllerConstructor: UpgradeController, identifier: 'w-upgrade' },
];
