import React from 'react';
import { expect } from 'chai';
import { shallow } from 'enzyme';
import '../stubs';

import Icon from '../../src/components/icon/Icon';

describe('Icon', () => {
  it('exists', () => {
    // eslint-disable-next-line no-unused-expressions
    expect(Icon).to.exist;
  });

  it('has just icon classes by default', () => {
    expect(shallow(<Icon name="test" />).is('.icon.icon-test')).to.equal(true);
  });

  it('has additional classes if specified', () => {
    expect(shallow(<Icon name="test" className="icon-red icon-big" />).prop('className')).to.contain('icon-red icon-big');
  });
});
