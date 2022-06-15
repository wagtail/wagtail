import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import initCollapsibleBreadcrumbs from '../../../../../client/src/includes/breadcrumbs';
import template from './breadcrumb-next.html';

const { docs, argTypes } = generateDocs(template);

document.addEventListener('DOMContentLoaded', () => {
  initCollapsibleBreadcrumbs();
});

export default {
  parameters: { docs },
  argTypes: { ...argTypes },
};

const Template = (args) => (
  <header>
    <Pattern filename={__filename} context={args} />
  </header>
);

export const Base = Template.bind({});

Base.args = {
  pages: [
    {
      is_root: true,
      id: 2,
      get_admin_display_title: 'Root item',
    },
    {
      id: 3,
      get_admin_display_title: 'First item',
    },
  ],
};

export const WithTrailingTitle = Template.bind({});

WithTrailingTitle.args = {
  pages: [
    {
      is_root: true,
      id: 2,
      get_admin_display_title: 'Root item',
    },
    {
      id: 3,
      get_admin_display_title: 'First item',
    },
    {
      id: 4,
      get_admin_display_title: 'Second item',
    },
    {
      id: 5,
      get_admin_display_title: 'Third item',
    },
  ],
  trailing_breadcrumb_title: 'Trailing item',
};

export const MultipleItems = Template.bind({});

MultipleItems.args = {
  pages: [
    {
      is_root: true,
      id: 2,
      get_admin_display_title: 'Root item',
    },
    {
      id: 3,
      get_admin_display_title: 'First item',
    },
    {
      id: 4,
      get_admin_display_title: 'Second item',
    },
    {
      id: 5,
      get_admin_display_title: 'Third item',
    },
    {
      id: 4,
      get_admin_display_title: 'Fourth item',
    },
    {
      id: 5,
      get_admin_display_title: 'Fifth item',
    },
  ],
};
