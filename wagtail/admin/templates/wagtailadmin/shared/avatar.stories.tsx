import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './avatar.html';

const { docs, argTypes } = generateDocs(template);

export default {
  parameters: { docs },
  argTypes: {
    ...argTypes,
    size: {
      defaultValue: 'default',
      options: ['small', 'default', 'large'],
      control: { type: 'select' },
    },
    storybook_json: {
      table: {
        disable: true,
      },
    },
  },
};

// Used to convert storybook_json into usable data for this story
const formatArgTypeJson = (text: string) => {
  try {
    // Replace single quotes and convert text to json object
    return Object.assign({}, ...JSON.parse(text.replace(/'/g, '"')));
  } catch (e) {
    console.log(e);
  }
};

const Template = ({ url, size, username }) => {
  // Use argTypes from template to populate tag overrides 😎
  const tagKeys = formatArgTypeJson(argTypes.storybook_json.description);

  return (
    <Pattern
      filename={__filename}
      tags={{
        ...(tagKeys && {
          avatar_url: {
            [tagKeys[size]]: {
              raw: url,
            },
          },
        }),
      }}
      context={{ size, username }}
    />
  );
};

export const Uploaded = Template.bind({});
Uploaded.args = {
  size: 'default',
  url: 'https://source.unsplash.com/6eaMM0BuWVI/100x100',
  username: '',
};

export const Gravatar = Template.bind({});
Gravatar.args = {
  size: 'default',
  url: 'https://gravatar.com/avatar/31c3d5cc27d1faa321c2413589e8a53f?s=200&d=robohash&r=x',
  username: 'Robot',
};
