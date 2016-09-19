import React from 'react';
import { expect } from 'chai';
import { shallow } from 'enzyme';

import '../stubs';
import Explorer from '../../src/components/explorer/Explorer';
import ExplorerItem from '../../src/components/explorer/ExplorerItem';

describe('Explorer', () => {
  it('exists', () => {
    expect(Explorer).to.be.a('function');
  });

  describe('ExplorerItem', () => {
    const props = {
      data: {
        meta: {
            children: {
                count: 0,
            }
        }
      },
    };

    it('exists', () => {
      expect(ExplorerItem).to.be.a('function');
    });

    it('has item metadata', () => {
        expect(shallow(<ExplorerItem {...props} />).find('.c-explorer__meta')).to.have.lengthOf(1);
    });

    it('metadata contains item type', () => {
        expect(shallow(<ExplorerItem {...props} typeName="Foo" />).find('.c-explorer__meta').text()).to.contain('Foo');
    });
  });
});
