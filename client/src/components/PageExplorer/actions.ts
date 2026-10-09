import { ThunkAction } from 'redux-thunk';

import * as admin from '../../api/admin';
import { MAX_EXPLORER_PAGES } from '../../config/wagtailConfig';
import { createAction } from '../../utils/actions';

import { Action, State } from './reducers';

type ThunkActionType = ThunkAction<void, State, unknown, Action>;

const getPageStart = createAction('GET_PAGE_START', (id: number) => ({ id }));
const getPageSuccess = createAction(
  'GET_PAGE_SUCCESS',
  (id: number, data: admin.WagtailExplorerAPI, offset: number) => ({
    id,
    data,
    offset,
  }),
);
const getPageFailure = createAction(
  'GET_PAGE_FAILURE',
  (id: number, error: Error) => ({ id, error }),
);

/**
 * Gets a page, its translations, and its children from the API.
 */
function getPage(id: number, offset = 0): ThunkActionType {
  return (dispatch, getState) => {
    dispatch(getPageStart(id));

    return admin.getExplorerPage(id, { offset }).then(
      (data) => {
        const nbPages = offset + data.children.items.length;
        dispatch(getPageSuccess(id, data, offset));

        // Stop if the response was discarded as stale, e.g. the explorer was
        // closed and reopened while loading, so a newer request is in charge.
        const page = getState().nodes[id];
        if (!page || page.children.items.length !== nbPages) {
          return;
        }

        // Load more pages if necessary. Only one request is created even though
        // more might be needed, thus naturally throttling the loading.
        if (nbPages < data.children.count && nbPages < MAX_EXPLORER_PAGES) {
          dispatch(getPage(id, nbPages));
        }
      },
      (error) => {
        dispatch(getPageFailure(id, error));
      },
    );
  };
}

const openPageExplorerPrivate = createAction('OPEN_EXPLORER', (id) => ({ id }));
export const closePageExplorer = createAction('CLOSE_EXPLORER');

export function openPageExplorer(id: number): ThunkActionType {
  return (dispatch) => {
    dispatch(openPageExplorerPrivate(id));
    dispatch(getPage(id));
  };
}

const gotoPagePrivate = createAction(
  'GOTO_PAGE',
  (id: number, transition: number) => ({ id, transition }),
);

export function gotoPage(id: number, transition: number): ThunkActionType {
  return (dispatch, getState) => {
    const { nodes } = getState();
    const page = nodes[id];

    // Pages that were only listed as children or translations of another page
    // need to be loaded to get their parent, translations, and children.
    // Start loading before navigating, so the node exists when it is rendered.
    if (!page || (!page.isLoaded && !page.isFetching)) {
      dispatch(getPage(id));
    }

    dispatch(gotoPagePrivate(id, transition));
  };
}
