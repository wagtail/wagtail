import React from 'react';
import { shallow } from 'enzyme';
import PageChooserResultSet from './PageChooserResultSet';

describe('PageChooserResultSet', () => {
  it('renders', () => {
    expect(shallow((
      <PageChooserResultSet
        onPageChosen={() => {}}
        onNavigate={() => {}}
        onChangePage={() => {}}
        totalPages={0}
      />
    ))).toMatchSnapshot();
  });
});
