import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';

import * as actions from './actions';

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);

const stubState = {
  explorer: {
    isVisible: true,
  },
  nodes: {
    5: {
      isFetching: true,
      children: {},
    },
  },
};

describe('actions', () => {
  describe('openPageExplorer', () => {
    it('exists', () => {
      expect(actions.openPageExplorer).toBeDefined();
    });

    it('open', () => {
      const stub = { ...stubState };
      stub.explorer.isVisible = false;
      const store = mockStore(stub);
      store.dispatch(actions.openPageExplorer(5));
      expect(store.getActions()).toMatchSnapshot();
    });

    it('open first time', () => {
      const stub = { explorer: stubState.explorer, nodes: {} };
      stub.explorer.isVisible = false;
      const store = mockStore(stub);
      store.dispatch(actions.openPageExplorer(5));
      expect(store.getActions()).toMatchSnapshot();
    });

    it('open at root', () => {
      const stub = { ...stubState };
      stub.explorer.isVisible = false;
      const store = mockStore(stub);
      store.dispatch(actions.openPageExplorer(1));
      expect(store.getActions()).toMatchSnapshot();
    });
  });

  describe('closePageExplorer', () => {
    it('exists', () => {
      expect(actions.closePageExplorer).toBeDefined();
    });

    it('close', () => {
      const store = mockStore(stubState);
      store.dispatch(actions.closePageExplorer());
      expect(store.getActions()).toMatchSnapshot();
    });
  });

  describe('gotoPage', () => {
    it('exists', () => {
      expect(actions.gotoPage).toBeDefined();
    });

    it('creates action', () => {
      const store = mockStore(stubState);
      store.dispatch(actions.gotoPage(5, 1));
      expect(store.getActions()).toMatchSnapshot();
    });

    it('triggers getChildren', () => {
      const stub = { ...stubState };
      stub.nodes[5].isFetching = false;
      const store = mockStore(stub);
      store.dispatch(actions.gotoPage(5, 1));
      expect(store.getActions()).toMatchSnapshot();
    });
  });
});
