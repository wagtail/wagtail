import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './tab_nav_link.html';

const { docs, argTypes } = generateDocs(template);

export default {
  title: 'Shared / Tabs / TabsNavLink',
  parameters: { docs },
  argTypes: { ...argTypes },
};

const Template = (args) => <Pattern filename={__filename} context={args} />;

export const Base = Template.bind({});

Base.args = {
  tab_id: 'tasks',
  title: 'Tasks',
};

export const Errors = Template.bind({});

Errors.args = {
  tab_id: 'content',
  title: 'Content',
  errors_count: 35,
};
