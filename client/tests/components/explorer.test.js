import React from 'react';
import { expect } from 'chai';
import { shallow, mount, render } from 'enzyme';
import '../stubs';

import Explorer from '../../src/components/explorer/Explorer';

describe('Explorer', () => {
  it('exists', () => {
    expect(Explorer).to.exist;
  });

  it('contains spec with an expectation', () => {
    expect(shallow(<Explorer />).contains(<div className="c-explorer" />)).to.equal(true);
  });

  it('contains spec with an expectation', () => {
    expect(shallow(<Explorer />).is('.c-explorer')).to.equal(true);
  });

  it('contains spec with an expectation', () => {
    expect(mount(<Explorer />).find('.c-explorer').length).to.equal(1);
  });
});
