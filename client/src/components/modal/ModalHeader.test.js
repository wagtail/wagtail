import React from 'react';
import { shallow } from 'enzyme';
import ModalHeader from './ModalHeader';

describe('ModalHeader', () => {
  it('renders', () => {
    expect(shallow((
      <ModalHeader
        onSearch={() => {}}
        searchEnabled={false}
      />
    ))).toMatchSnapshot();
  });
});
