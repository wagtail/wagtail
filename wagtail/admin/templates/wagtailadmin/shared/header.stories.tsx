import React from 'react';
import TemplatePattern from '../../../../../client/storybook/TemplatePattern';

import template from './header.html';

export default {
  parameters: {
    docs: {
      source: { code: template },
      // Trial generating documentation from comment within the template. To be replaced by a better pattern.
      extractComponentDescription: () =>
        template
          .match(/{% comment %}\n((.|\n)+){% endcomment %}/m)[1]
          .replace(/ {4}/g, ''),
    },
  },
  argTypes: {
    icon: {
      options: window.WAGTAIL_ICONS,
      control: { type: 'select' },
      description: 'name of an icon to place against the title',
    },
  },
};

const Template = (args) => (
  <TemplatePattern filename={__filename} context={args} />
);

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
