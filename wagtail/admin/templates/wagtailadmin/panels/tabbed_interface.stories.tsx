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
    visible_children: [
      {
        heading: 'Content',
        render_as_object: `<h2>Content</h2><div>Content Body</div>`,
      },
      {
        heading: 'Promote',
        render_as_object: `<h2>Promote</h2><div>Promote Body</div>`,
      },
      {
        heading: 'Settings',
        render_as_object: `<h2>Settings</h2><div>Settings Body</div>`,
      },
    ],
  },
};

export const Single = Template.bind({});

Single.args = {
  self: {
    visible_children: [
      {
        heading: 'Tab1',
        render_as_object: `<h2>Title1</h2><div>Body Text</div>`,
      },
    ],
  },
};

export const Multiple = Template.bind({});

Multiple.args = {
  self: {
    visible_children: [
      {
        heading: 'Tab1',
        render_as_object: `<h1>Title 1</h1><div>Body Text</div>`,
      },
      {
        heading: 'Tab2',
        render_as_object: `<h1>Title 2</h1><div>Body Text</div>`,
      },
      {
        heading: 'Tab3',
        render_as_object: `<h1>Title 3</h1><div>Body Text</div>`,
      },
      {
        heading: 'Tab4',
        render_as_object: `<h1>Title 4</h1><div>Body Text</div>`,
      },
      {
        heading: 'Tab5',
        render_as_object: `<h1>Title 5</h1><div>Body Text</div>`,
      },
    ],
  },
};
