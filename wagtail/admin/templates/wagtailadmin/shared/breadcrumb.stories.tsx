import React from 'react';
import TemplatePattern from '../../../../../client/storybook/TemplatePattern';

import template from './breadcrumb.html';
import docs from './breadcrumb.md';

export default {
  parameters: {
    docs: {
      source: { code: template },
      extractComponentDescription: () => docs,
    },
  },
};

const Template = (args) => (
  <TemplatePattern filename={__filename} context={args} />
);

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
