import React from 'react';
import { shallow } from 'enzyme';

import PageCount from './PageCount';

const mockProps = {
  page: {
    id: 1,
    children: {
      count: 1,
    },
  },
};

describe('PageCount', () => {
  it('exists', () => {
    expect(PageCount).toBeDefined();
  });

  it('works', () => {
    expect(shallow(<PageCount {...mockProps} />)).toMatchSnapshot();
  });

  it('plural', () => {
    const props = { ...mockProps };
    props.page.children.count = 5;
    expect(shallow(<PageCount {...props} />)).toMatchSnapshot();
  });
});
