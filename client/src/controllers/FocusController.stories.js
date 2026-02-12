import React from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { FocusController } from './FocusController';

export default {
  title: 'Stimulus / FocusController',
  argTypes: { debug: { control: 'boolean', defaultValue: false } },
};

const definitions = [
  { controllerConstructor: FocusController, identifier: 'w-focus' },
];

const Template = ({ debug = false }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <a
      href="#main"
      id="skip"
      data-controller="w-focus"
      data-action="w-focus#focus:prevent"
    >
      Skip to main content
    </a>
    <main id="main">
      <button type="button" className="button button-small">
        First focusable element in main
      </button>
      <h3 className="top">Top header</h3>
      <p style={{ height: '120vh' }}>Very long content</p>
      <button
        type="button"
        className="button button-small button-secondary"
        data-controller="w-focus"
        data-action="w-focus#focus"
        data-w-focus-target-value=".top"
      >
        Back to top
      </button>
    </main>
  </StimulusWrapper>
);

export const Base = Template.bind({});
