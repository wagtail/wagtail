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

const handleClick = () => {
  const counterElement = document.getElementById('counter');
  const currentCount = parseInt(counterElement.innerText.split(' ')[2], 10);
  counterElement.innerText = `Click count: ${currentCount + 1}`;
};

const Template = ({ debug = false, count = 0 }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <button
      type="button"
      className="button button-small button-secondary"
      data-controller="w-kbd"
      data-w-kbd-key-value="mod+j"
      onClick={handleClick}
    >
      Click Me
    </button>
    <p id="counter">Click count: {count}</p>
    <p>
      {' '}
      Trigger with <kbd> Command ⌘</kbd> + <kbd>j</kbd> on macOS or{' '}
      <kbd>Ctrl</kbd> + <kbd>j</kbd> on Windows
    </p>
  </StimulusWrapper>
);

export const Base = Template.bind({});
