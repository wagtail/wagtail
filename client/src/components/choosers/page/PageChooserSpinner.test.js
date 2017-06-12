import React from 'react';
import { shallow } from 'enzyme';
import PageChooserSpinner from './PageChooserSpinner';

describe('PageChooserSpinner', () => {
  it('renders', () => {
    expect(shallow((
      <PageChooserSpinner>
        Test
      </PageChooserSpinner>
    ))).toMatchSnapshot();
  });

  it('#isActive', () => {
    expect(shallow((
      <PageChooserSpinner isActive={true}>
        Test
      </PageChooserSpinner>
    ))).toMatchSnapshot();
  });
});
