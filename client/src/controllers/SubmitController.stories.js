import React, { useState } from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { SubmitController } from './SubmitController';

export default {
  title: 'Stimulus / SubmitController',
  argTypes: {
    debug: {
      control: 'boolean',
      defaultValue: false,
    },
  },
};

const definitions = [
  {
    identifier: 'w-submit',
    controllerConstructor: SubmitController,
  },
];

const Template = ({ debug = false }) => {
  const [submitCount, updateSubmitCount] = useState(0);

  return (
    <StimulusWrapper debug={debug} definitions={definitions}>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          updateSubmitCount(submitCount + 1);
        }}
      >
        <select
          name="order"
          defaultValue="A-Z"
          data-action="w-submit#submit"
          data-controller="w-submit"
        >
          <option value="num">Numerical</option>
          <option value="A-Z">A to Z</option>
          <option value="Z-A">Z to A</option>
        </select>
      </form>
      <p>
        Form has been submitted <strong>{submitCount}</strong> times.
      </p>
    </StimulusWrapper>
  );
};

export const Base = Template.bind({});
