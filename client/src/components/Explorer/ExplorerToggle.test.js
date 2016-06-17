import React from 'react';
import { createStore } from 'redux';
import { shallow } from 'enzyme';

import ExplorerToggle from './ExplorerToggle';
import rootReducer from './reducers';

const store = createStore(rootReducer);

describe('ExplorerToggle', () => {
  it('exists', () => {
    expect(ExplorerToggle).toBeDefined();
  });

  it('basic', () => {
    expect(shallow(<ExplorerToggle store={store} />)).toMatchSnapshot();
  });

  it('loading state', (done) => {
    store.subscribe(() => {
      expect(shallow(<ExplorerToggle store={store} />)).toMatchSnapshot();
      done();
    });

    store.dispatch({ type: 'FETCH_START' });
  });

  it('#children', () => {
    expect(shallow((
      <ExplorerToggle store={store}>
        <span>
          To infinity and beyond!
        </span>
      </ExplorerToggle>
    ))).toMatchSnapshot();
  });
});
