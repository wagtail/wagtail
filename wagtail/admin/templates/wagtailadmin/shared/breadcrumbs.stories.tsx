import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import { StimulusWrapper } from '../../../../../client/storybook/StimulusWrapper';
import { RevealController } from '../../../../../client/src/controllers/RevealController';

import template from './breadcrumbs.html';

const { docs, argTypes } = generateDocs(template);

export default {
  title: 'Shared / Breadcrumbs',
  parameters: { docs },
  argTypes: { ...argTypes },
};

const Template = (args) => (
  <StimulusWrapper
    definitions={[
      { identifier: 'w-breadcrumbs', controllerConstructor: RevealController },
    ]}
  >
    <header>
      <Pattern filename={__filename} context={args} />
    </header>
  </StimulusWrapper>
);

export const Base = Template.bind({});

Base.args = {
  items: [
    {
      url: '/admin/snippets/',
      label: 'Snippets',
    },
    {
      url: '/admin/snippets/people/',
      label: 'People',
    },
    {
      url: '/admin/snippets/people/1/',
      label: 'Muddy Waters',
    },
  ],
};

export const WithNonLinkItem = Template.bind({});

WithNonLinkItem.args = {
  items: [
    {
      url: '/admin/snippets/',
      label: 'Snippets',
    },
    {
      url: '/admin/snippets/people/',
      label: 'People',
    },
    {
      label: 'New: Person',
    },
  ],
};

export const Expanded = Template.bind({});

Expanded.args = {
  is_expanded: 'True',
  items: [
    {
      url: '/admin/snippets/',
      label: 'Snippets',
    },
    {
      url: '/admin/snippets/people/',
      label: 'People',
    },
    {
      url: '/admin/snippets/people/1/',
      label: 'Muddy Waters',
    },
  ],
};
