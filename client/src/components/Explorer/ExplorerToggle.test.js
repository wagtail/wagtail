import React from 'react';
import { shallow } from 'enzyme';
import configureMockStore from 'redux-mock-store';

import ExplorerToggle from './ExplorerToggle';

const store = configureMockStore()({});

describe('ExplorerToggle', () => {
  it('exists', () => {
    expect(ExplorerToggle).toBeDefined();
  });

  it('basic', () => {
    expect(shallow((
      <ExplorerToggle store={store}>
        <span>
          To infinity and beyond!
        </span>
      </ExplorerToggle>
    ))).toMatchSnapshot();
  });

  describe('actions', () => {
    let wrapper;

    beforeEach(() => {
      store.dispatch = jest.fn();
      wrapper = shallow(<ExplorerToggle store={store}>Test</ExplorerToggle>);
    });

    it('onToggle', () => {
      wrapper.prop('onToggle')();
      expect(store.dispatch).toHaveBeenCalled();
    });
  });
});
