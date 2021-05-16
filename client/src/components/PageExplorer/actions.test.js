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
  describe('closePageExplorer', () => {
    it('exists', () => {
      expect(actions.closePageExplorer).toBeDefined();
    });

    it('creates action', () => {
      expect(actions.closePageExplorer().type).toEqual('CLOSE_EXPLORER');
    });
  });

  describe('togglePageExplorer', () => {
    it('exists', () => {
      expect(actions.togglePageExplorer).toBeDefined();
    });

    it('close', () => {
      const store = mockStore(stubState);
      store.dispatch(actions.togglePageExplorer(5));
      expect(store.getActions()).toMatchSnapshot();
    });

    it('open', () => {
      const stub = Object.assign({}, stubState);
      stub.explorer.isVisible = false;
      const store = mockStore(stub);
      store.dispatch(actions.togglePageExplorer(5));
      expect(store.getActions()).toMatchSnapshot();
    });

    it('open first time', () => {
      const stub = { explorer: stubState.explorer, nodes: {} };
      stub.explorer.isVisible = false;
      const store = mockStore(stub);
      store.dispatch(actions.togglePageExplorer(5));
      expect(store.getActions()).toMatchSnapshot();
    });

    it('open at root', () => {
      const stub = Object.assign({}, stubState);
      stub.explorer.isVisible = false;
      const store = mockStore(stub);
      store.dispatch(actions.togglePageExplorer(1));
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
      const stub = Object.assign({}, stubState);
      stub.nodes[5].isFetching = false;
      const store = mockStore(stub);
      store.dispatch(actions.gotoPage(5, 1));
      expect(store.getActions()).toMatchSnapshot();
    });
  });
});
