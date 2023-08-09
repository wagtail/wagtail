import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './whats_new_in_wagtail_version.html';

const { docs, argTypes } = generateDocs(template);

export default {
  title: 'Home / New in Wagtail',
  parameters: { docs },
  argTypes: { ...argTypes },
};

const Template = (args) => <Pattern filename={__filename} context={args} />;

export const Base = Template.bind({});
Base.args = {
  version: '99',
  dismissible_id: 'aabbcc',
  editor_guide_link: 'https://guide.wagtail.org/',
};
