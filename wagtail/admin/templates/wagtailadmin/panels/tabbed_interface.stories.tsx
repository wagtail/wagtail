import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';
import { initTabs } from '../../../../../client/src/includes/tabs';
import template from './tabbed_interface.html';

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
});

const { docs, argTypes } = generateDocs(template);

export default {
  title: 'Shared / Tabs / TabbedInterface',
  parameters: { docs },
  argTypes: { ...argTypes },
};

const Template = (args) => <Pattern filename={__filename} context={args} />;

export const Base = Template.bind({});

Base.args = {
  self: {
    visible_children_with_identifiers: [
      [
        {
          heading: 'Content',
          render_as_object: `<h2>Content</h2><div>Content Body</div>`,
        },
        'content',
      ],
      [
        {
          heading: 'Promote',
          render_as_object: `<h2>Promote</h2><div>Promote Body</div>`,
        },
        'promote',
      ],
      [
        {
          heading: 'Settings',
          render_as_object: `<h2>Settings</h2><div>Settings Body</div>`,
        },
        'settings',
      ],
    ],
  },
};

export const Single = Template.bind({});

Single.args = {
  self: {
    visible_children_with_identifiers: [
      [
        {
          heading: 'Tab1',
          render_as_object: `<h2>Title1</h2><div>Body Text</div>`,
        },
        '1',
      ],
    ],
  },
};

export const Multiple = Template.bind({});

Multiple.args = {
  self: {
    visible_children_with_identifiers: [
      [
        {
          heading: 'Tab1',
          render_as_object: `<h1>Title 1</h1><div>Body Text</div>`,
        },
        '1',
      ],
      [
        {
          heading: 'Tab2',
          render_as_object: `<h1>Title 2</h1><div>Body Text</div>`,
        },
        '2',
      ],
      [
        {
          heading: 'Tab3',
          render_as_object: `<h1>Title 3</h1><div>Body Text</div>`,
        },
        '3',
      ],
      [
        {
          heading: 'Tab4',
          render_as_object: `<h1>Title 4</h1><div>Body Text</div>`,
        },
        '4',
      ],
      [
        {
          heading: 'Tab5',
          render_as_object: `<h1>Title 5</h1><div>Body Text</div>`,
        },
        '5',
      ],
    ],
  },
};
