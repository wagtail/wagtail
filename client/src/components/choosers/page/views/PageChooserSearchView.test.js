import React from 'react';
import { shallow } from 'enzyme';
import PageChooserSearchView from './PageChooserSearchView';

describe('PageChooserSearchView', () => {
  it('renders', () => {
    expect(shallow((
      <PageChooserSearchView
        onPageChosen={() => {}}
        onNavigate={() => {}}
        pageTypes={{}}
        totalItems={0}
      />
    ))).toMatchSnapshot();
  });
});
