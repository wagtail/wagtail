import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './page_status_tag.html';

const { docs, argTypes } = generateDocs(template);

export default {
  parameters: { docs },
  argTypes: {
    ...argTypes,
    url: {
      options: [null, 'https://wagtail.io'],
    },
  },
};

const Template = (args) => (
  <Pattern filename={__filename} context={{ page: args }} />
);
export const Live = Template.bind({});

Live.args = {
  live: true,
  status_string: 'live',
  url: null,
};

export const Draft = Template.bind({});

Draft.args = {
  live: false,
  status_string: 'draft',
};
