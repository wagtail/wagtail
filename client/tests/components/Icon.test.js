import React from 'react';
import { expect } from 'chai';
import { shallow } from 'enzyme';
import '../stubs';

import Icon from '../../src/components/icon/Icon';

describe('Icon', () => {
  it('exists', () => {
    expect(Icon).to.be.a('function');
  });

  it('has just icon classes by default', () => {
    expect(shallow(<Icon name="test" />).is('.icon.icon-test')).to.equal(true);
  });

  it('has additional classes if specified', () => {
    expect(shallow(<Icon name="test" className="icon-red icon-big" />).prop('className')).to.contain('icon-red icon-big');
  });

  it('has no accessible label by default', () => {
    expect(shallow(<Icon name="test" />).children().isEmpty()).to.equal(true);
  });

  it('has accessible label if specified', () => {
    const label = shallow(<Icon name="test" title="For screen readers" />).childAt(0);
    expect(label.text()).to.contain('For screen readers');
    expect(label.html()).to.contain('aria-role="presentation"');
  });
});
