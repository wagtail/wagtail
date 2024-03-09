import React from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { KeyboardController } from './KeyboardController';

export default {
    title: 'Stimulus / KeyboardController',
    argTypes: {
      debug: {
        control: 'boolean',
        defaultValue: false,
      },
    },
  };


const definitions = [
    {
        identifier: 'w-kbd',
        controllerConstructor: KeyboardController,
    },
];

const Template = ({ debug = false }) => (
    <StimulusWrapper debug={debug} definitions={definitions}>
      <button
        type="button"
        className="button button-small button-secondary"
        data-controller="w-kbd"
        data-w-kbd-key-value="mod+j"
        onClick={() => console.log('clicked')}
      >
       Click Me
      </button>
  
      <p> Trigger with <kbd> Command ⌘</kbd> + <kbd>j</kbd> on macOS or <kbd>Ctrl</kbd> + <kbd>j</kbd> on Windows</p>
    </StimulusWrapper>
  );

export const Base = Template.bind({});