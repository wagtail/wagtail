import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './avatar.html';

const { docs, argTypes } = generateDocs(template);

export default {
  title: 'Shared / Avatar',
  parameters: {
    docs,
  },
  argTypes: {
    ...argTypes,
    size: {
      options: [null, 'small', 'large', 'square'],
    },
  },
};

const Template = (args) => <Pattern filename={__filename} context={args} />;

export const Base = Template.bind({});
Base.args = {
  size: 'null',
};

export const Small = Template.bind({});
Small.args = {
  size: 'small',
};

export const Large = Template.bind({});
Large.args = {
  size: 'large',
};

export const Square = Template.bind({});
Square.args = {
  size: 'square',
};
