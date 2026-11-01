import { combineReducers } from 'redux';
import configureMockStore from 'redux-mock-store';
import { thunk } from 'redux-thunk';

import { getExplorerPage } from '../../api/admin';
import * as actions from './actions';
import explorer from './reducers/explorer';
import nodes from './reducers/nodes';

jest.mock('../../api/admin', () => ({
  getExplorerPage: jest.fn((id) =>
    Promise.resolve({
      page: { id, meta: { depth: 3 } },
      translations: [],
      children: { count: 0, items: [] },
    }),
  ),
}));

jest.mock('../../config/wagtailConfig', () => ({
  ...jest.requireActual('../../config/wagtailConfig'),
  MAX_EXPLORER_PAGES: 50,
}));

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);
const rootReducer = combineReducers({ explorer, nodes });

// A mock store whose state follows the dispatched actions, for actions that
// read back the state they produced
const mockReducedStore = (initialState) =>
  mockStore((dispatchedActions) =>
    dispatchedActions.reduce(rootReducer, initialState),
  );

const flushPromises = () =>
  new Promise((resolve) => {
    setTimeout(resolve, 0);
  });

const getActionTypes = (store) => store.getActions().map(({ type }) => type);

const stubState = {
  explorer: {
    isVisible: true,
  },
  nodes: {
    5: {
      isFetching: false,
      isLoaded: true,
      children: {},
      meta: { depth: 3 },
    },
  },
};

describe('actions', () => {
  afterEach(() => {
    getExplorerPage.mockClear();
  });

  describe('openPageExplorer', () => {
    it('exists', () => {
      expect(actions.openPageExplorer).toBeDefined();
    });

    it('open', () => {
      const store = mockReducedStore({
        explorer: { isVisible: false },
        nodes: {},
      });
      store.dispatch(actions.openPageExplorer(5));
      expect(store.getActions()).toMatchSnapshot();
      expect(getExplorerPage).toHaveBeenCalledWith(5, { offset: 0 });
    });

    it('loads the page', async () => {
      const store = mockReducedStore({
        explorer: { isVisible: false },
        nodes: {},
      });
      store.dispatch(actions.openPageExplorer(5));
      await flushPromises();
      expect(getActionTypes(store)).toEqual([
        'OPEN_EXPLORER',
        'GET_PAGE_START',
        'GET_PAGE_SUCCESS',
      ]);
      expect(store.getActions()[2].payload).toEqual({
        id: 5,
        offset: 0,
        data: {
          page: { id: 5, meta: { depth: 3 } },
          translations: [],
          children: { count: 0, items: [] },
        },
      });
    });

    it('loads more children when needed', async () => {
      const items = (start, count) =>
        Array.from({ length: count }, (_, i) => ({ id: 100 + start + i }));
      getExplorerPage
        .mockResolvedValueOnce({
          page: { id: 5, meta: { depth: 3 } },
          translations: [],
          children: { count: 30, items: items(0, 20) },
        })
        .mockResolvedValueOnce({
          page: { id: 5, meta: { depth: 3 } },
          translations: [],
          children: { count: 30, items: items(20, 10) },
        });

      const store = mockReducedStore({
        explorer: { isVisible: false },
        nodes: {},
      });
      store.dispatch(actions.openPageExplorer(5));
      await flushPromises();

      expect(getExplorerPage).toHaveBeenCalledTimes(2);
      expect(getExplorerPage).toHaveBeenNthCalledWith(2, 5, { offset: 20 });
    });

    it('stops loading more children at MAX_EXPLORER_PAGES', async () => {
      const response = {
        page: { id: 5, meta: { depth: 3 } },
        translations: [],
        children: {
          count: 1000,
          items: Array.from({ length: 20 }, (_, i) => ({ id: 100 + i })),
        },
      };
      getExplorerPage
        .mockResolvedValueOnce(response)
        .mockResolvedValueOnce(response)
        .mockResolvedValueOnce(response);

      const store = mockReducedStore({
        explorer: { isVisible: false },
        nodes: {},
      });
      store.dispatch(actions.openPageExplorer(5));
      await flushPromises();

      // Stops after 60 pages, as 60 >= MAX_EXPLORER_PAGES (mocked to 50)
      expect(getExplorerPage).toHaveBeenCalledTimes(3);
    });

    it('discards more children requested before reopening', async () => {
      const items = (start, count) =>
        Array.from({ length: count }, (_, i) => ({ id: 100 + start + i }));
      const response = (start, count) => ({
        page: { id: 5, meta: { depth: 3 } },
        translations: [],
        children: { count: 30, items: items(start, count) },
      });
      let resolveStale;
      getExplorerPage
        .mockResolvedValueOnce(response(0, 20))
        .mockReturnValueOnce(
          new Promise((resolve) => {
            resolveStale = resolve;
          }),
        )
        .mockResolvedValueOnce(response(0, 20))
        .mockResolvedValueOnce(response(20, 10));

      const store = mockReducedStore({
        explorer: { isVisible: false },
        nodes: {},
      });
      store.dispatch(actions.openPageExplorer(5));
      await flushPromises();

      // Reopen while the second batch of children is still loading
      store.dispatch(actions.closePageExplorer());
      store.dispatch(actions.openPageExplorer(5));
      await flushPromises();
      expect(getExplorerPage).toHaveBeenCalledTimes(4);

      resolveStale(response(20, 10));
      await flushPromises();

      // The stale response is discarded and does not trigger more requests
      expect(getExplorerPage).toHaveBeenCalledTimes(4);
      expect(store.getState().nodes[5].children.items).toEqual(
        items(0, 30).map(({ id }) => id),
      );
    });

    it('handles errors', async () => {
      getExplorerPage.mockRejectedValueOnce(new Error('Not Found'));
      const store = mockReducedStore({
        explorer: { isVisible: false },
        nodes: {},
      });
      store.dispatch(actions.openPageExplorer(5));
      await flushPromises();
      expect(getActionTypes(store)).toEqual([
        'OPEN_EXPLORER',
        'GET_PAGE_START',
        'GET_PAGE_FAILURE',
      ]);
    });
  });

  describe('closePageExplorer', () => {
    it('exists', () => {
      expect(actions.closePageExplorer).toBeDefined();
    });

    it('close', () => {
      const store = mockReducedStore(stubState);
      store.dispatch(actions.closePageExplorer());
      expect(store.getActions()).toMatchSnapshot();
    });
  });

  describe('gotoPage', () => {
    it('exists', () => {
      expect(actions.gotoPage).toBeDefined();
    });

    it('does not reload a loaded page', () => {
      const store = mockReducedStore(stubState);
      store.dispatch(actions.gotoPage(5, 1));
      expect(store.getActions()).toMatchSnapshot();
      expect(getExplorerPage).not.toHaveBeenCalled();
    });

    it('does not reload a page that is being loaded', () => {
      const store = mockReducedStore({
        ...stubState,
        nodes: { 5: { isFetching: true, isLoaded: false, meta: {} } },
      });
      store.dispatch(actions.gotoPage(5, 1));
      expect(getExplorerPage).not.toHaveBeenCalled();
    });

    it('loads a page only known from a listing, before navigating', () => {
      const store = mockReducedStore({
        ...stubState,
        nodes: { 7: { isFetching: false, isLoaded: false, meta: {} } },
      });
      store.dispatch(actions.gotoPage(7, 1));
      expect(getActionTypes(store)).toEqual(['GET_PAGE_START', 'GOTO_PAGE']);
      expect(getExplorerPage).toHaveBeenCalledWith(7, { offset: 0 });
    });

    it('loads an unknown page, e.g. the parent of the starting page', () => {
      const store = mockReducedStore({ ...stubState, nodes: {} });
      store.dispatch(actions.gotoPage(2, -1));
      expect(getActionTypes(store)).toEqual(['GET_PAGE_START', 'GOTO_PAGE']);
      expect(getExplorerPage).toHaveBeenCalledWith(2, { offset: 0 });
    });
  });
});
