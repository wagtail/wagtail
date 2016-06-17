import React from 'react';
import { shallow } from 'enzyme';

import ExplorerItem from './ExplorerItem';

const mockProps = {
  data: {
    meta: {
      children: {
        count: 0,
      }
    }
  },
};

describe('ExplorerItem', () => {
  it('exists', () => {
    expect(ExplorerItem).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<ExplorerItem />)).toMatchSnapshot();
  });

  it('#data', () => {
    expect(shallow(<ExplorerItem {...mockProps} />)).toMatchSnapshot();
  });

  it('#typeName', () => {
    expect(shallow(<ExplorerItem {...mockProps} typeName="Foo" />)).toMatchSnapshot();
  });
});
