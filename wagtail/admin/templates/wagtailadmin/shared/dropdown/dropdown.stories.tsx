import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import { StimulusWrapper } from '../../../../../../client/storybook/StimulusWrapper';
import { DropdownController } from '../../../../../../client/src/controllers/DropdownController';

import template from './dropdown.html';

const { docs, argTypes } = generateDocs(template);

export default {
  title: 'Shared / Dropdown',
  parameters: {
    docs,
  },
  argTypes: {
    ...argTypes,
    toggle_icon: {
      control: 'select',
      options: [null, ...window.WAGTAIL_ICONS],
    },
  },
  decorators: [
    (Story) => (
      <StimulusWrapper
        debug
        definitions={[
          {
            identifier: 'w-dropdown',
            controllerConstructor: DropdownController,
          },
        ]}
      >
        <Story />
      </StimulusWrapper>
    ),
  ],
};

const Template = (args) => <Pattern filename={__filename} context={args} />;

export const Base = Template.bind({});
Base.args = {
  toggle_icon: 'dots-horizontal',
  toggle_aria_label: 'Actions',
  children: `
  <a href="">Link</a>
  <a href=""><svg class="icon icon-order" aria-hidden="true"><use href="#icon-order"></use></svg>Link with icon</a>
  <button type="button">Button</button>
  <button type="button"><svg class="icon icon-order" aria-hidden="true"><use href="#icon-order"></use></svg>Button with icon</button>
`,
};
