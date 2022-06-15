import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './breadcrumb.html';

const { docs } = generateDocs(template);

export default {
  parameters: { docs },
};

const Template = (args) => <Pattern filename={__filename} context={args} />;

export const Base = Template.bind({});

Base.args = {
  pages: [
    {
      is_root: true,
      id: 2,
      get_admin_display_title: 'First item',
    },
    {
      id: 3,
      get_admin_display_title: 'Second item',
    },
    {
      id: 4,
      get_admin_display_title: 'Third item',
    },
  ],
};
