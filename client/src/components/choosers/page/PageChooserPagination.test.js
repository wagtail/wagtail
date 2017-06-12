import React from 'react';
import { shallow } from 'enzyme';
import PageChooserPagination from './PageChooserPagination';

describe('PageChooserPagination', () => {
  it('renders', () => {
    expect(shallow((
      <PageChooserPagination
        totalPages={0}
        onChangePage={() => {}}
      />
    ))).toMatchSnapshot();
  });

  it('has pages', () => {
    expect(shallow((
      <PageChooserPagination
        totalPages={2}
        onChangePage={() => {}}
      />
    ))).toMatchSnapshot();
  });
});
