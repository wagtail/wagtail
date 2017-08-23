import React from 'react';
import { shallow } from 'enzyme';

import PublicationStatus from './PublicationStatus';

describe('PublicationStatus', () => {
  it('exists', () => {
    expect(PublicationStatus).toBeDefined();
  });

  it('#status live', () => {
    expect(shallow((
      <PublicationStatus
        status={{
          status: 'live + draft',
          live: true,
          has_unpublished_changes: true,
        }}
      />
    ))).toMatchSnapshot();
  });

  it('#status not live', () => {
    expect(shallow((
      <PublicationStatus
        status={{
          status: 'live + draft',
          live: false,
          has_unpublished_changes: true,
        }}
      />
    ))).toMatchSnapshot();
  });
});
