import React, { useState } from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { AutoFieldController } from './AutoFieldController';

export default {
  title: 'Shared / AutoFieldController',
  argTypes: {
    debug: {
      control: 'boolean',
      defaultValue: false,
    },
  },
};

const definitions = [
  {
    identifier: 'w-auto-field',
    controllerConstructor: AutoFieldController,
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
          data-action="w-auto-field#submit"
          data-controller="w-auto-field"
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
