import type { Definition } from '@hotwired/stimulus';

// Order controller imports alphabetically.
import { ActionController } from './ActionController';
import { AutosizeController } from './AutosizeController';
import { BulkController } from './BulkController';
import { CloneController } from './CloneController';
import { CountController } from './CountController';
import { DialogController } from './DialogController';
import { DismissibleController } from './DismissibleController';
import { DropdownController } from './DropdownController';
import { InitController } from './InitController';
import { ProgressController } from './ProgressController';
import { RevealController } from './RevealController';
import { SkipLinkController } from './SkipLinkController';
import { SlugController } from './SlugController';
import { SubmitController } from './SubmitController';
import { SwapController } from './SwapController';
import { SyncController } from './SyncController';
import { TagController } from './TagController';
import { TeleportController } from './TeleportController';
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
  { controllerConstructor: CloneController, identifier: 'w-clone' },
  { controllerConstructor: CloneController, identifier: 'w-messages' },
  { controllerConstructor: CountController, identifier: 'w-count' },
  { controllerConstructor: DialogController, identifier: 'w-dialog' },
  { controllerConstructor: DismissibleController, identifier: 'w-dismissible' },
  { controllerConstructor: DropdownController, identifier: 'w-dropdown' },
  { controllerConstructor: InitController, identifier: 'w-init' },
  { controllerConstructor: ProgressController, identifier: 'w-progress' },
  { controllerConstructor: RevealController, identifier: 'w-breadcrumbs' },
  { controllerConstructor: RevealController, identifier: 'w-reveal' },
  { controllerConstructor: SkipLinkController, identifier: 'w-skip-link' },
  { controllerConstructor: SlugController, identifier: 'w-slug' },
  { controllerConstructor: SubmitController, identifier: 'w-submit' },
  { controllerConstructor: SwapController, identifier: 'w-swap' },
  { controllerConstructor: SyncController, identifier: 'w-sync' },
  { controllerConstructor: TagController, identifier: 'w-tag' },
  { controllerConstructor: TeleportController, identifier: 'w-teleport' },
  { controllerConstructor: TooltipController, identifier: 'w-tooltip' },
  { controllerConstructor: UpgradeController, identifier: 'w-upgrade' },
];
