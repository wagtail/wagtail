import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './header.html';

const { docs, argTypes } = generateDocs(template);

export default {
  parameters: {
    docs,
  },
  argTypes: {
    ...argTypes,
    icon: {
      options: window.WAGTAIL_ICONS,
      control: { type: 'select' },
      description: 'name of an icon to place against the title',
    },
  },
};

const Template = (args) => <Pattern filename={__filename} context={args} />;

export const Base = Template.bind({});

Base.args = {
  title: 'Calendar',
  icon: 'date',
};

export const Action = Template.bind({});

Action.args = {
  title: 'Users',
  subtitle: 'Editors',
  icon: 'user',
  action_url: '/test/',
  action_text: 'Add',
};
