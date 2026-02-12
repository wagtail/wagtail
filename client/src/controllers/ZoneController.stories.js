import React from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { ZoneController } from './ZoneController';

export default {
  title: 'Stimulus / ZoneController',
  argTypes: {
    debug: {
      control: 'boolean',
      defaultValue: false,
    },
  },
};

const definitions = [
  {
    identifier: 'w-zone',
    controllerConstructor: ZoneController,
  },
];

const Template = ({ debug = false }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <div
      className="drop-zone"
      data-controller="w-zone"
      data-w-zone-active-class="hovered"
      data-action="
        dragover->w-zone#activate:prevent
        dragleave->w-zone#deactivate
        dragend->w-zone#deactivate
        drop->w-zone#deactivate:prevent
      "
    >
      Drag something here
    </div>

    <p>
      Drag an item over the box, and drop it to see class activation and
      deactivation in action.
    </p>
  </StimulusWrapper>
);

export const Base = Template.bind({});
