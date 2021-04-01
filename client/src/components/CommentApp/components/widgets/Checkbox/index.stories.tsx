import React from 'react';

import { Styling } from '../../../utils/storybook';

import Checkbox from '.';

export default { title: 'Checkbox' };

export function checkbox() {
  const [checked, setChecked] = React.useState(false);

  return (
    <>
      <Styling />
      <Checkbox
        id="id"
        label="Checkbox"
        checked={checked}
        onChange={setChecked}
      />
    </>
  );
}
