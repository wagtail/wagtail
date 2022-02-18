import React from 'react';
import TemplatePattern from '../../../../../client/storybook/TemplatePattern';

import template from './animated_logo.html';

export default {
  parameters: {
    docs: {
      source: { code: template },
    },
  },
};

export const AnimatedLogo = () => <TemplatePattern filename={__filename} />;
