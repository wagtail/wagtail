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
  describe('closeExplorer', () => {
    it('exists', () => {
      expect(actions.closeExplorer).toBeDefined();
    });

    it('creates action', () => {
      expect(actions.closeExplorer().type).toEqual('CLOSE_EXPLORER');
    });
  });

  describe('toggleExplorer', () => {
    it('exists', () => {
      expect(actions.toggleExplorer).toBeDefined();
    });

    it('close', () => {
      const store = mockStore(stubState);
      store.dispatch(actions.toggleExplorer(5));
      expect(store.getActions()).toMatchSnapshot();
    });

    it('open', () => {
      const stub = Object.assign({}, stubState);
      stub.explorer.isVisible = false;
      const store = mockStore(stub);
      store.dispatch(actions.toggleExplorer(5));
      expect(store.getActions()).toMatchSnapshot();
    });

    it('open first time', () => {
      const stub = { explorer: stubState.explorer, nodes: {} };
      stub.explorer.isVisible = false;
      const store = mockStore(stub);
      store.dispatch(actions.toggleExplorer(5));
      expect(store.getActions()).toMatchSnapshot();
    });

    it('open at root', () => {
      const stub = Object.assign({}, stubState);
      stub.explorer.isVisible = false;
      const store = mockStore(stub);
      store.dispatch(actions.toggleExplorer(1));
      expect(store.getActions()).toMatchSnapshot();
    });
  });

  describe('popPage', () => {
    it('exists', () => {
      expect(actions.popPage).toBeDefined();
    });

    it('works', () => {
      expect(actions.popPage().type).toEqual('POP_PAGE');
    });
  });

  describe('pushPage', () => {
    it('exists', () => {
      expect(actions.pushPage).toBeDefined();
    });

    it('creates action', () => {
      const store = mockStore(stubState);
      store.dispatch(actions.pushPage(5));
      expect(store.getActions()).toMatchSnapshot();
    });

    it('triggers getChildren', () => {
      const stub = Object.assign({}, stubState);
      stub.nodes[5].isFetching = false;
      const store = mockStore(stub);
      store.dispatch(actions.pushPage(5));
      expect(store.getActions()).toMatchSnapshot();
    });
  });
});
