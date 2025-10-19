import React from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { AutosizeController } from './AutosizeController';

export default {
  title: 'Stimulus / AutosizeController',
  argTypes: {
    value: {
      control: 'text',
      defaultValue: '',
    },
    debug: {
      control: 'boolean',
      defaultValue: false,
    },
  },
};

const definitions = [
  {
    identifier: 'w-autosize',
    controllerConstructor: AutosizeController,
  },
];

const Template = ({ value = '', debug = false }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <textarea data-controller="w-autosize" defaultValue={value} />
  </StimulusWrapper>
);

export const EmptyTextarea = Template.bind({});

export const FilledTextarea = Template.bind({});

FilledTextarea.args = {
  value:
    'This is a filled textarea, it should autosize to fit its content. Wagtail ipsum dolor sit flap, perching by the riverside with elegant wiggle. Tiny steps, gentle dips, and endless tail-bobs bring joy to every puddle. Curabitur chirp elit, sed flutter magna finibus et song. Praesent feathers shimmer in early light; nullam breeze dapibus whisper across soft meadow moss. Etiam wagtailus curious, hopping between stones and stories, always following ripples where sunlight dances.',
};
