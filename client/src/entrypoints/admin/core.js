import $ from 'jquery';
import * as StimulusModule from '@hotwired/stimulus';

import { Icon, Portal } from '../..';
import { coreControllerDefinitions } from '../../controllers';
import { escapeHtml } from '../../utils/text';
import { InlinePanel } from '../../components/InlinePanel';
import { MultipleChooserPanel } from '../../components/MultipleChooserPanel';
import { initStimulus } from '../../includes/initStimulus';

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

window.wagtail = wagtail;

window.escapeHtml = escapeHtml;

window.InlinePanel = InlinePanel;

window.MultipleChooserPanel = MultipleChooserPanel;

$(() => {
  /* Dropzones */
  $('.drop-zone')
    .on('dragover', function onDragOver() {
      $(this).addClass('hovered');
    })
    .on('dragleave dragend drop', function onDragLeave() {
      $(this).removeClass('hovered');
    });
});
