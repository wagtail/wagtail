import React from 'react';
import { shallow } from 'enzyme';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware, combineReducers } from 'redux';
import thunkMiddleware from 'redux-thunk';
import * as actions from './actions';
import explorer from './reducers/explorer';
import nodes from './reducers/nodes';
import Explorer from './Explorer';
import { PagesAPI } from '../../api/admin';
import { ADMIN_API } from '../../config/wagtailConfig';

const rootReducer = combineReducers({
  explorer,
  nodes,
});

const store = createStore(rootReducer, {}, applyMiddleware(thunkMiddleware));

const api = new PagesAPI(ADMIN_API.PAGES, ADMIN_API.EXTRA_CHILDREN_PARAMETERS);
store.dispatch(actions.setApi(api));

describe('Explorer', () => {
  it('exists', () => {
    expect(Explorer).toBeDefined();
  });

  it('renders', () => {
    expect(shallow(<Explorer store={store} />)).toMatchSnapshot();
    expect(shallow(<Provider store={store}><Explorer /></Provider>)).toMatchSnapshot();
  });

  it('visible', () => {
    store.dispatch(actions.toggleExplorer(1));
    expect(shallow(<Explorer store={store} />)).toMatchSnapshot();
    expect(shallow(<Explorer store={store} />).dive()).toMatchSnapshot();
  });

  describe('actions', () => {
    let wrapper;

    beforeEach(() => {
      store.dispatch = jest.fn();
      wrapper = shallow(<Explorer store={store} />);
    });

    it('pushPage', () => {
      wrapper.prop('pushPage')();
      expect(store.dispatch).toHaveBeenCalled();
    });

    it('popPage', () => {
      wrapper.prop('popPage')();
      expect(store.dispatch).toHaveBeenCalled();
    });

    it('onClose', () => {
      wrapper.prop('onClose')();
      expect(store.dispatch).toHaveBeenCalled();
    });
  });
});
