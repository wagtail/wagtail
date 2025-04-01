import type { Definition } from '@hotwired/stimulus';

// Order controller imports alphabetically.
import { ActionController } from './ActionController';
import { AutosizeController } from './AutosizeController';
import { BlockController } from './BlockController';
import { BulkController } from './BulkController';
import { ClipboardController } from './ClipboardController';
import { CloneController } from './CloneController';
import { CountController } from './CountController';
import { DialogController } from './DialogController';
import { DismissibleController } from './DismissibleController';
import { DrilldownController } from './DrilldownController';
import { DropdownController } from './DropdownController';
import { FocusController } from './FocusController';
import { FormsetController } from './FormsetController';
import { InitController } from './InitController';
import { KeyboardController } from './KeyboardController';
import { LocaleController } from './LocaleController';
import { OrderableController } from './OrderableController';
import { PreviewController } from './PreviewController';
import { ProgressController } from './ProgressController';
import { RevealController } from './RevealController';
import { RulesController } from './RulesController';
import { SessionController } from './SessionController';
import { SlugController } from './SlugController';
import { SubmitController } from './SubmitController';
import { SwapController } from './SwapController';
import { SyncController } from './SyncController';
import { TagController } from './TagController';
import { TeleportController } from './TeleportController';
import { TooltipController } from './TooltipController';
import { UnsavedController } from './UnsavedController';
import { UpgradeController } from './UpgradeController';
import { ZoneController } from './ZoneController';

/**
 * Important: Only add default core controllers that should load with the base admin JS bundle.
 */
export const coreControllerDefinitions: Definition[] = [
  // Keep this list in alphabetical order
  { controllerConstructor: ActionController, identifier: 'w-action' },
  { controllerConstructor: AutosizeController, identifier: 'w-autosize' },
  { controllerConstructor: BlockController, identifier: 'w-block' },
  { controllerConstructor: BulkController, identifier: 'w-bulk' },
  { controllerConstructor: ClipboardController, identifier: 'w-clipboard' },
  { controllerConstructor: CloneController, identifier: 'w-clone' },
  { controllerConstructor: CloneController, identifier: 'w-messages' },
  { controllerConstructor: CountController, identifier: 'w-count' },
  { controllerConstructor: DialogController, identifier: 'w-dialog' },
  { controllerConstructor: DismissibleController, identifier: 'w-dismissible' },
  { controllerConstructor: DrilldownController, identifier: 'w-drilldown' },
  { controllerConstructor: DropdownController, identifier: 'w-dropdown' },
  { controllerConstructor: FocusController, identifier: 'w-focus' },
  { controllerConstructor: FormsetController, identifier: 'w-formset' },
  { controllerConstructor: InitController, identifier: 'w-init' },
  { controllerConstructor: KeyboardController, identifier: 'w-kbd' },
  { controllerConstructor: LocaleController, identifier: 'w-locale' },
  { controllerConstructor: OrderableController, identifier: 'w-orderable' },
  { controllerConstructor: PreviewController, identifier: 'w-preview' },
  { controllerConstructor: ProgressController, identifier: 'w-progress' },
  { controllerConstructor: RevealController, identifier: 'w-breadcrumbs' },
  { controllerConstructor: RevealController, identifier: 'w-reveal' },
  { controllerConstructor: RulesController, identifier: 'w-rules' },
  { controllerConstructor: SessionController, identifier: 'w-session' },
  { controllerConstructor: SlugController, identifier: 'w-slug' },
  { controllerConstructor: SubmitController, identifier: 'w-submit' },
  { controllerConstructor: SwapController, identifier: 'w-swap' },
  { controllerConstructor: SyncController, identifier: 'w-sync' },
  { controllerConstructor: TagController, identifier: 'w-tag' },
  { controllerConstructor: TeleportController, identifier: 'w-teleport' },
  { controllerConstructor: TooltipController, identifier: 'w-tooltip' },
  { controllerConstructor: UnsavedController, identifier: 'w-unsaved' },
  { controllerConstructor: UpgradeController, identifier: 'w-upgrade' },
  { controllerConstructor: ZoneController, identifier: 'w-zone' },
];
