import React from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { ActionController } from './ActionController';

export default {
  title: 'Shared / ActionController',
  argTypes: {
    debug: {
      control: 'boolean',
      defaultValue: false,
    },
  },
};

const definitions = [
  {
    identifier: 'w-action',
    controllerConstructor: ActionController,
  },
];

const Template = ({ debug = false }) => {
  return (
    <StimulusWrapper debug={debug} definitions={definitions}>
      <button
        type="button"
        className="button button-small button-secondary"
        data-action="w-action#post"
        data-controller="w-action"
        data-w-action-redirect-value="false"
        data-w-action-url-value={window.location.href}
      >
        Lock
      </button>

      <p>Click to lock post and redirect</p>
    </StimulusWrapper>
  );
};

export const Base = Template.bind({});
