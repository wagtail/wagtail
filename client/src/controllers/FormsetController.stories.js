import React, { useState } from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { FormsetController } from './FormsetController';

export default {
  title: 'Stimulus / FormsetController',
  argTypes: {
    debug: {
      control: 'boolean',
      defaultValue: false,
    },
  },
};

const definitions = [
  {
    identifier: 'w-formset',
    controllerConstructor: FormsetController,
  },
];

const Template = ({ debug = false }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <form data-controller="w-formset">
      <input
        type="hidden"
        name="form-TOTAL_FORMS"
        value="2"
        data-w-formset-target="totalFormsInput"
      />
      <input
        type="hidden"
        name="form-MIN_NUM_FORMS"
        value="0"
        data-w-formset-target="minFormsInput"
      />
      <input
        type="hidden"
        name="form-MAX_NUM_FORMS"
        value="50"
        data-w-formset-target="maxFormsInput"
      />
      <input type="hidden" name="form-INITIAL_FORMS" value="2" />
      <ul data-w-formset-target="forms">
        <li data-w-formset-target="child">
          <input type="text" name="form-0-name" />
          <input
            type="hidden"
            name="form-0-DELETE"
            data-w-formset-target="deleteInput"
          />
          <button type="button" data-action="w-formset#delete">
            Delete
          </button>
        </li>
        <li data-w-formset-target="child">
          <input type="text" name="form-1-name" />
          <input
            type="hidden"
            name="form-1-DELETE"
            data-w-formset-target="deleteInput"
          />
          <button type="button" data-action="w-formset#delete">
            Delete
          </button>
        </li>
      </ul>
      <button data-action="w-formset#add" type="button">
        Add
      </button>
      <template
        data-w-formset-target="template"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{
          __html: `
        <li data-w-formset-target="child">
          <input type="text" name="form-__prefix__-name" />
          <input type="hidden" name="form-__prefix__-DELETE" data-w-formset-target="deleteInput" />
          <button type="button" data-action="w-formset#delete">Delete </button>
        </li>`,
        }}
      />
    </form>
  </StimulusWrapper>
);

export const Base = Template.bind({});
