import React from 'react';
import {Pattern, generateDocs} from 'storybook-django/src/react';

import template from './user_avatar.html';

const {docs, argTypes} = generateDocs(template);

export default {
  parameters: {docs},
  argTypes: {...argTypes},
};

const Template = (args) => <Pattern filename={__filename} context={args}/>;
export const Base = Template.bind({});

Base.args = {
  user: {
    pk: 1,
    first_name: 'Timmy',
    last_name: 'Newtron',
    username: 'theTim',
    wagtail_userprofile: {
      name: 'Someone else',
      avatar: {
        url: "https://gravatar.com/avatar/31c3d5cc27d1faa321c2413589e8a53f?s=200&d=robohash&r=x"
      }
    },
  },
  // username: 'Timothy',
}


