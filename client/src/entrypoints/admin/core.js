import * as StimulusModule from '@hotwired/stimulus';

import { Icon, Portal } from '../..';
import { coreControllerDefinitions } from '../../controllers';
import { InlinePanel } from '../../components/InlinePanel';
import { MultipleChooserPanel } from '../../components/MultipleChooserPanel';
import { WAGTAIL_CONFIG } from '../../config/wagtailConfig';
import { initStimulus } from '../../includes/initStimulus';

import { urlify } from '../../utils/urlify';
import { escapeHtml } from '../../utils/text';

/** Expose a global to allow for customisations and packages to build with Stimulus. */
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

/**
 * Support legacy global URLify which can be called with `allowUnicode` as a third param.
 * Was not documented and only used in modeladmin prepopulate JS.
 *
 * @deprecated RemovedInWagtail70
 * @see https://github.com/django/django/blob/main/django/contrib/admin/static/admin/js/urlify.js#L156
 *
 * @param {string} str
 * @param {number} numChars
 * @param {boolean} allowUnicode
 * @returns {string}
 */
window.URLify = (str, numChars = 255, allowUnicode = false) =>
  urlify(str, { numChars, allowUnicode });
