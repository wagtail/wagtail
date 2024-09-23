import React from 'react';
import { Pattern, generateDocs } from 'storybook-django/src/react';

import template from './help_block.html';

const { docs, argTypes } = generateDocs(template);

export default {
  title: 'Shared / Help Block',
  parameters: { docs },
  argTypes: { ...argTypes },
};

const HelpBlock = (props) => <Pattern filename={__filename} context={props} />;

export const Base = () => (
  <>
    <HelpBlock status="info">Help block info message</HelpBlock>
    <HelpBlock status="warning">Help block warning message</HelpBlock>
    <HelpBlock status="critical">Help block critical message</HelpBlock>
  </>
);
