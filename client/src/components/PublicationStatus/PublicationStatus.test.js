import { shallow } from 'enzyme';
import React from 'react';

import PublicationStatus from './PublicationStatus';

describe('PublicationStatus', () => {
  it('exists', () => {
    expect(PublicationStatus).toBeDefined();
  });

  it('#status live', () => {
    expect(
      shallow(<PublicationStatus status="live + draft" live />),
    ).toMatchSnapshot();
  });

  it('#status not live', () => {
    expect(
      shallow(<PublicationStatus status="live + draft" live={false} />),
    ).toMatchSnapshot();
  });
});
