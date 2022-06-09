import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './user_avatar.html';

const { docs, argTypes } = generateDocs(template);

export default {
  parameters: { docs },
  argTypes: { ...argTypes },
};

const Template = ({ url }) => (
  <Pattern
    filename={__filename}
    tags={{
      avatar_url: {
        'user size=25': {
          raw: url,
        },
      },
    }}
  />
);

export const Uploaded = Template.bind({});
Uploaded.args = {
  url: 'https://source.unsplash.com/6eaMM0BuWVI/100x100',
};

export const Gravatar = Template.bind({});
Gravatar.args = {
  url: 'https://gravatar.com/avatar/31c3d5cc27d1faa321c2413589e8a53f?s=200&d=robohash&r=x',
};
