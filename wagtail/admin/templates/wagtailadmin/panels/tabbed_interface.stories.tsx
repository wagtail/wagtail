import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';
import template from './tabbed_interface.html';
import { TabsController } from '../../../../../client/src/controllers/TabsController';
import { StimulusWrapper } from '../../../../../client/storybook/StimulusWrapper';

const { docs, argTypes } = generateDocs(template);

export default {
  title: 'Shared / Tabs / TabbedInterface',
  parameters: { docs },
  argTypes: { ...argTypes },
};

const Template = ({ debug = false, ...args }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <Pattern filename={__filename} context={args} />
  </StimulusWrapper>
);

const baseAttrs = {
  'data-controller': 'w-tabs',
  'data-action': 'popstate@window->w-tabs#select',
  'data-w-tabs-use-location-value': 'true',
};

const buildTabs = (tabbedInterface) => ({
  ...tabbedInterface,
  attrs: baseAttrs,
  visible_children_with_identifiers:
    tabbedInterface.visible_children_with_identifiers.map(
      ([child, identifier]) => [
        {
          ...child,
          show_panel_furniture: true,
        },
        identifier,
      ],
    ),
});

const definitions = [
  { identifier: 'w-tabs', controllerConstructor: TabsController },
];

export const Base = Template.bind({});

Base.args = {
  self: buildTabs({
    visible_children_with_identifiers: [
      [
        {
          heading: 'Content',
          render_html: `<h2>Content</h2><div>Content Body</div>`,
        },
        'content',
      ],
      [
        {
          heading: 'Promote',
          render_html: `<h2>Promote</h2><div>Promote Body</div>`,
        },
        'promote',
      ],
      [
        {
          heading: 'Settings',
          render_html: `<h2>Settings</h2><div>Settings Body</div>`,
        },
        'settings',
      ],
    ],
  }),
};

export const Single = Template.bind({});

Single.args = {
  self: buildTabs({
    visible_children_with_identifiers: [
      [
        {
          heading: 'Tab1',
          render_html: `<h2>Title1</h2><div>Body Text</div>`,
        },
        '1',
      ],
    ],
  }),
};

export const Multiple = Template.bind({});

Multiple.args = {
  self: buildTabs({
    visible_children_with_identifiers: [
      [
        {
          heading: 'Tab1',
          render_html: `<h1>Title 1</h1><div>Body Text</div>`,
        },
        '1',
      ],
      [
        {
          heading: 'Tab2',
          render_html: `<h1>Title 2</h1><div>Body Text</div>`,
        },
        '2',
      ],
      [
        {
          heading: 'Tab3',
          render_html: `<h1>Title 3</h1><div>Body Text</div>`,
        },
        '3',
      ],
      [
        {
          heading: 'Tab4',
          render_html: `<h1>Title 4</h1><div>Body Text</div>`,
        },
        '4',
      ],
      [
        {
          heading: 'Tab5',
          render_html: `<h1>Title 5</h1><div>Body Text</div>`,
        },
        '5',
      ],
    ],
  }),
};
