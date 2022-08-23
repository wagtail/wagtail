import React, { useState } from 'react';

import Stories from '../includes/stimulus.stories';

import { AutoFormController } from './AutoFormController';

export default {
  title: 'Stimulus/AutoFormController',
  argTypes: {
    debug: {
      control: 'boolean',
      defaultValue: false,
    },
  },
};

const Template = ({ debug = false }) => {
  const [submitCount, updateSubmitCount] = useState(0);

  return (
    <Stories.StimulusWrapper
      controllers={{ 'w-auto-form': AutoFormController }}
      debug={debug}
    >
      <form
        onSubmit={(event) => {
          event.preventDefault();
          updateSubmitCount(submitCount + 1);
        }}
      >
        <select
          name="order"
          defaultValue="A-Z"
          data-action="w-auto-form#submit"
          data-controller="w-auto-form"
        >
          <option value="num">Numerical</option>
          <option value="A-Z">A to Z</option>
          <option value="Z-A">Z to A</option>
        </select>
      </form>
      <p>
        Form has been submitted <strong>{submitCount}</strong> times.
      </p>
    </Stories.StimulusWrapper>
  );
};

export const Base = Template.bind({});
