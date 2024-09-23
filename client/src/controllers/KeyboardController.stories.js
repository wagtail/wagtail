import React, { useState } from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { KeyboardController } from './KeyboardController';

export default {
  title: 'Stimulus / KeyboardController',
  argTypes: {
    debug: { control: 'boolean', defaultValue: false },
  },
};

const definitions = [
  { identifier: 'w-kbd', controllerConstructor: KeyboardController },
];

const Template = ({ debug = false }) => {
  const [count, setCount] = useState(0);
  return (
    <StimulusWrapper debug={debug} definitions={definitions}>
      <button
        type="button"
        className="button button-small button-secondary"
        data-controller="w-kbd"
        data-w-kbd-key-value="mod+j"
        onClick={() => {
          setCount((stateCount) => stateCount + 1);
        }}
      >
        Add to count
      </button>
      <button
        type="button"
        className="button button-small button-secondary"
        data-controller="w-kbd"
        aria-keyshortcuts=";"
        onClick={() => {
          setCount(0);
        }}
      >
        Clear count
      </button>
      <div>
        <p>
          Add to count with <kbd> Command ⌘</kbd> + <kbd>j</kbd> on macOS or{' '}
          <kbd>Ctrl</kbd> + <kbd>j</kbd> on Windows.
        </p>
        <p>
          Clear found with <kbd>;</kbd>
        </p>
      </div>
      <p id="counter">
        Click count: <strong>{count}</strong>
      </p>
    </StimulusWrapper>
  );
};

export const Base = Template.bind({});
