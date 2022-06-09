import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './page_status_tag_new.html';

const { docs, argTypes } = generateDocs(template);

export default {
  parameters: { docs },
  argTypes: { ...argTypes },
};

const PublicTemplate = (args) => (
  <Pattern
    filename={__filename}
    tags={{
      test_page_is_public: {
        'page as is_public': {
          raw: false,
        },
      },
    }}
    context={{ page: args }}
  />
);

export const Public = PublicTemplate.bind({});
Public.args = {
  live: true,
  url: '#',
};

const PrivateTemplate = (args) => (
  <Pattern
    filename={__filename}
    tags={{
      test_page_is_public: {
        'page as is_public': {
          raw: true,
        },
      },
    }}
    context={{ page: args }}
  />
);

export const Private = PrivateTemplate.bind({});
Private.args = {
  live: true,
  url: '#',
};
