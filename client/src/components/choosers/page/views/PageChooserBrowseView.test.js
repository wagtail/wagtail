import React from 'react';
import { shallow } from 'enzyme';
import PageChooserBrowseView from './PageChooserBrowseView';

describe('PageChooserBrowseView', () => {
  it('renders', () => {
    expect(shallow((
      <PageChooserBrowseView
        onPageChosen={() => {}}
        onNavigate={() => {}}
        pageTypes={{}}u
      />
    ))).toMatchSnapshot();
  });
});
