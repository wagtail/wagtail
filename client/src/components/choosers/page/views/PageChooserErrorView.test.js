import React from 'react';
import { shallow } from 'enzyme';
import PageChooserErrorView from './PageChooserErrorView';

describe('PageChooserErrorView', () => {
  it('renders', () => {
    expect(shallow((
      <PageChooserErrorView errorMessage="test" />
    ))).toMatchSnapshot();
  });
});
