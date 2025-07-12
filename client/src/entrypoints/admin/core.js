import * as StimulusModule from '@hotwired/stimulus';
import Telepath from 'telepath-unpack';

import { Icon, Portal } from '../..';
import { ExpandingFormset } from '../../components/ExpandingFormset';
import { coreControllerDefinitions } from '../../controllers';
import { Panel, PanelGroup, FieldPanel } from '../../components/Panel';
import { InlinePanel } from '../../components/InlinePanel';
import { MultipleChooserPanel } from '../../components/MultipleChooserPanel';
import { WAGTAIL_CONFIG } from '../../config/wagtailConfig';
import { initStimulus } from '../../includes/initStimulus';

import { escapeHtml } from '../../utils/text';

/** Expose a global to allow for customizations and packages to build with Stimulus. */
window.StimulusModule = StimulusModule;

/**
 * Wagtail global module, useful for debugging and as the exposed
 * interface to access the Stimulus application instance and base
 * React components.
 *
 * @type {Object} wagtail
 * @property {Object} app - Wagtail's Stimulus application instance.
 * @property {Object} components - Exposed components as globals for third-party reuse.
 * @property {Object} components.Icon - Icon React component.
 * @property {Object} components.Portal - Portal React component.
 */
const wagtail = window.wagtail || {};

/** Initialise Wagtail Stimulus application with core controller definitions. */
wagtail.app = initStimulus({ definitions: coreControllerDefinitions });

/** Expose components as globals for third-party reuse. */
wagtail.components = { Icon, Portal };

/** Expose a global for undocumented third-party usage. */
window.wagtailConfig = WAGTAIL_CONFIG;

window.wagtail = wagtail;

window.escapeHtml = escapeHtml;

window.InlinePanel = InlinePanel;

window.MultipleChooserPanel = MultipleChooserPanel;

if (!window.telepath) {
  window.telepath = new Telepath();
}

window.telepath.register('wagtail.panels.Panel', Panel);
window.telepath.register('wagtail.panels.PanelGroup', PanelGroup);
window.telepath.register('wagtail.panels.FieldPanel', FieldPanel);

/**
 * Support legacy, undocumented, usage of `buildExpandingFormset` as a global function.
 * @deprecated RemovedInWagtail80
 */
function buildExpandingFormset(prefix, opts = {}) {
  return new ExpandingFormset(prefix, opts);
}

window.buildExpandingFormset = buildExpandingFormset;
