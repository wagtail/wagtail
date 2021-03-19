import React from 'react';
import { shallow } from 'enzyme';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware, combineReducers } from 'redux';
import thunkMiddleware from 'redux-thunk';
import * as actions from './actions';
import explorer from './reducers/explorer';
import nodes from './reducers/nodes';
import Explorer from './Explorer';

const rootReducer = combineReducers({
  explorer,
  nodes,
});

const store = createStore(rootReducer, {}, applyMiddleware(thunkMiddleware));

describe('Explorer', () => {
  it('exists', () => {
    expect(Explorer).toBeDefined();
  });

  it('renders', () => {
    expect(shallow(<Explorer store={store} />).dive()).toMatchSnapshot();
    expect(shallow(<Provider store={store}><Explorer /></Provider>).dive()).toMatchSnapshot();
  });

  it('visible', () => {
    store.dispatch(actions.toggleExplorer(1));
    expect(shallow(<Explorer store={store} />).dive()).toMatchSnapshot();
    expect(shallow(<Explorer store={store} />).dive().dive()).toMatchSnapshot();
  });

  describe('actions', () => {
    let wrapper;

    beforeEach(() => {
      store.dispatch = jest.fn();
      wrapper = shallow(<Explorer store={store} />);
    });

    it('gotoPage', () => {
      wrapper.dive().prop('gotoPage')();
      expect(store.dispatch).toHaveBeenCalled();
    });

    it('onClose', () => {
      wrapper.dive().prop('onClose')();
      expect(store.dispatch).toHaveBeenCalled();
    });
  });
});
