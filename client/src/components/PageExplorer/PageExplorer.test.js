import React from 'react';
import { shallow } from 'enzyme';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware, combineReducers } from 'redux';
import thunkMiddleware from 'redux-thunk';
import * as actions from './actions';
import explorer from './reducers/explorer';
import nodes from './reducers/nodes';
import PageExplorer from './PageExplorer';

const rootReducer = combineReducers({
  explorer,
  nodes,
});

const store = createStore(rootReducer, {}, applyMiddleware(thunkMiddleware));

describe('PageExplorer', () => {
  it('exists', () => {
    expect(PageExplorer).toBeDefined();
  });

  it('renders', () => {
    expect(shallow(<PageExplorer store={store} />).dive()).toMatchSnapshot();
    expect(
      shallow(
        <Provider store={store}>
          <PageExplorer />
        </Provider>,
      ).dive(),
    ).toMatchSnapshot();
  });

  it('visible', () => {
    store.dispatch(actions.openPageExplorer(1));
    expect(shallow(<PageExplorer store={store} />).dive()).toMatchSnapshot();
    expect(
      shallow(<PageExplorer store={store} />)
        .dive()
        .dive(),
    ).toMatchSnapshot();
  });

  describe('actions', () => {
    let wrapper;

    beforeEach(() => {
      store.dispatch = jest.fn();
      wrapper = shallow(<PageExplorer store={store} />);
    });

    it('gotoPage', () => {
      wrapper.dive().prop('gotoPage')();
      expect(store.dispatch).toHaveBeenCalled();
    });
  });
});
