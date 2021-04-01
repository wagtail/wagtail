import React from 'react';

import { Styling } from '../../../utils/storybook';

import Radio from '.';

export default { title: 'Radio' };

export function radio() {
  const [value, setValue] = React.useState<string | null>(null);

  return (
    <>
      <Styling />
      <Radio
        id="option-1"
        name="test"
        value="option-1"
        label="Option one"
        checked={value === 'option-1'}
        onChange={setValue}
      />
      <Radio
        id="option-2"
        name="test"
        value="option-2"
        label="Option two"
        checked={value === 'option-2'}
        onChange={setValue}
      />
    </>
  );
}
