import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './status_tag.html';

const { docs, argTypes } = generateDocs(template);

export default {
  title: 'Shared / Status Tag',
  parameters: { docs },
  argTypes: {
    ...argTypes,
    classname: {
      options: [null, 'w-status--primary', 'w-status--label'],
    },
    url: {
      options: [null, 'https://wagtail.org/'],
    },
    title: {
      options: [null, 'wagtail live url'],
    },
    hidden_label: {
      options: [null, 'current status:'],
    },
  },
};

const Template = (args) => <Pattern filename={__filename} context={args} />;
export const Live = Template.bind({});

Live.args = {
  label: 'live',
  classname: null,
  url: null,
  title: null,
  hidden_label: null,
};
