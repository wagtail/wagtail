import React from 'react';
import { expect } from 'chai';
import { shallow } from 'enzyme';
import '../stubs';

import PublishStatus from '../../src/components/publish-status/PublishStatus';

describe('PublishStatus', () => {
  const status = {
    status: 'live + draft',
    live: true,
    has_unpublished_changes: true,
  };

  it('exists', () => {
    // eslint-disable-next-line no-unused-expressions
    expect(PublishStatus).to.exist;
  });

  // TODO Skipped because causing a test error.
  // Apparently this is fixed when using React 15.
  it.skip('does not render without status object', () => {
    expect(shallow(<PublishStatus />).isEmpty()).to.equal(true);
  });

  it('has label from object', () => {
    expect(shallow(<PublishStatus status={status} />).childAt(0).text()).to.contain(status.status);
  });

  it('has live class if live', () => {
    expect(shallow(<PublishStatus status={status} />).prop('className')).to.contain('c-status--live');
  });
});
