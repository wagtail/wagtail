import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import { CountController } from '../../../../../../client/src/controllers/CountController';
import { StimulusWrapper } from '../../../../../../client/storybook/StimulusWrapper';
import template from './tab_nav_link.html';

const { docs, argTypes } = generateDocs(template);

export default {
  title: 'Shared / Tabs / TabsNavLink',
  parameters: { docs },
  argTypes: { ...argTypes },
};

const definitions = [
  { identifier: 'w-count', controllerConstructor: CountController },
];

const Template = ({ debug = false, ...args }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <Pattern filename={__filename} context={args} />
    <div id={`tab-${args.tab_id}`}>
      {args.errors_count &&
        Array.from(Array(args.errors_count).keys()).map((i) => (
          <p className="error-message" key={i}>
            Error {i + 1}
          </p>
        ))}
    </div>
  </StimulusWrapper>
);

export const Base = Template.bind({});

Base.args = {
  tab_id: 'tasks',
  title: 'Tasks',
};

export const Errors = Template.bind({});

Errors.args = {
  tab_id: 'content',
  title: 'Content',
  errors_count: 3,
};
