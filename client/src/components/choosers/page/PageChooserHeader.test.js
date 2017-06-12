import React from 'react';
import { shallow } from 'enzyme';
import PageChooserHeader from './PageChooserHeader';

describe('PageChooserHeader', () => {
  it('renders', () => {
    expect(shallow((
      <PageChooserHeader
        onSearch={() => {}}
        searchEnabled={false}
      />
    ))).toMatchSnapshot();
  });
});
