import { ThunkAction } from 'redux-thunk';

import * as admin from '../../api/admin';
import { createAction } from '../../utils/actions';
import { MAX_EXPLORER_PAGES } from '../../config/wagtailConfig';

import { State as ExplorerState, Action as ExplorerAction } from './reducers/explorer';
import { State as NodeState, WagtailPageAPI, Action as NodeAction } from './reducers/nodes';

interface State {
  explorer: ExplorerState,
  nodes: NodeState,
}

type Action = ExplorerAction | NodeAction;
type ThunkActionType = ThunkAction<void, State, unknown, Action>;

const getPageSuccess = createAction('GET_PAGE_SUCCESS', (id: number, data: WagtailPageAPI) => ({ id, data }));
const getPageFailure = createAction('GET_PAGE_FAILURE', (id: number, error: Error) => ({ id, error }));

/**
 * Gets a page from the API.
 */
function getPage(id: number): ThunkActionType {
  return (dispatch) => admin.getPage(id).then((data) => {
    dispatch(getPageSuccess(id, data));
  }, (error) => {
    dispatch(getPageFailure(id, error));
  });
}

const getChildrenStart = createAction('GET_CHILDREN_START', (id: number) => ({ id }));
const getChildrenSuccess = createAction(
  'GET_CHILDREN_SUCCESS',
  (id, items: WagtailPageAPI[], meta: any) => ({ id, items, meta })
);
const getChildrenFailure = createAction('GET_CHILDREN_FAILURE', (id: number, error: Error) => ({ id, error }));

/**
 * Gets the children of a node from the API.
 */
function getChildren(id: number, offset = 0): ThunkActionType {
  return (dispatch) => {
    dispatch(getChildrenStart(id));

    return admin.getPageChildren(id, {
      offset: offset,
    }).then(({ items, meta }) => {
      const nbPages = offset + items.length;
      dispatch(getChildrenSuccess(id, items, meta));

      // Load more pages if necessary. Only one request is created even though
      // more might be needed, thus naturally throttling the loading.
      if (nbPages < meta.total_count && nbPages < MAX_EXPLORER_PAGES) {
        dispatch(getChildren(id, nbPages));
      }
    }, (error) => {
      dispatch(getChildrenFailure(id, error));
    });
  };
}

const openExplorer = createAction('OPEN_EXPLORER', id => ({ id }));
export const closeExplorer = createAction('CLOSE_EXPLORER');

export function toggleExplorer(id: number): ThunkActionType {
  return (dispatch, getState) => {
    const { explorer, nodes } = getState();

    if (explorer.isVisible) {
      dispatch(closeExplorer());
    } else {
      const page = nodes[id];

      dispatch(openExplorer(id));

      if (!page) {
        dispatch(getChildren(id));
      }

      // We need to get the title of the starting page, only if it is not the site's root.
      const isNotRoot = id !== 1;
      if (isNotRoot) {
        dispatch(getPage(id));
      }
    }
  };
}

export const popPage = createAction('POP_PAGE');
const pushPagePrivate = createAction('PUSH_PAGE', (id: number) => ({ id }));

export function pushPage(id: number): ThunkActionType {
  return (dispatch, getState) => {
    const { nodes } = getState();
    const page = nodes[id];

    dispatch(pushPagePrivate(id));

    if (page && !page.isFetching && !(page.children.count > 0)) {
      dispatch(getChildren(id));
    }
  };
}
