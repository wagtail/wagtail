import React from 'react';
import { shallow } from 'enzyme';
import ModalSpinner from './ModalSpinner';

describe('ModalSpinner', () => {
  it('renders', () => {
    expect(shallow((
      <ModalSpinner>
        Test
      </ModalSpinner>
    ))).toMatchSnapshot();
  });

  it('#isActive', () => {
    expect(shallow((
      <ModalSpinner isActive={true}>
        Test
      </ModalSpinner>
    ))).toMatchSnapshot();
  });
});
