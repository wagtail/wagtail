// TODO Move this file to the client/tests/components directory.
import React from 'react';
import { expect } from 'chai';
import { shallow, mount, render } from 'enzyme';
import '../stubs';

import Icon from '../../src/components/icon/Icon';

describe('Icon', () => {
  it('exists', () => {
    expect(Icon).to.exist;
  });

  it('contains spec with an expectation', () => {
    expect(shallow(<Icon />).contains(<div className="c-icon" />)).to.equal(true);
  });

  it('contains spec with an expectation', () => {
    expect(shallow(<Icon />).is('.c-icon')).to.equal(true);
  });

  it('contains spec with an expectation', () => {
    expect(mount(<Icon />).find('.c-icon').length).to.equal(1);
  });
});
