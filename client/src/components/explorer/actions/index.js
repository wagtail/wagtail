import { createAction } from 'redux-actions';

import { PAGES_ROOT_ID } from '../../../config/config';
import * as admin from '../../../api/admin';

export const fetchStart = createAction('FETCH_START');

export const fetchSuccess = createAction('FETCH_SUCCESS', (id, body) => ({ id, body }));

export const fetchFailure = createAction('FETCH_FAILURE');

export const pushPage = createAction('PUSH_PAGE');

export const popPage = createAction('POP_PAGE');

export const fetchBranchSuccess = createAction('FETCH_BRANCH_SUCCESS', (id, json) => ({ id, json }));

export const fetchBranchStart = createAction('FETCH_BRANCH_START');

export const clearError = createAction('CLEAR_TRANSPORT_ERROR');

export const resetTree = createAction('RESET_TREE');

export const treeResolved = createAction('TREE_RESOLVED');

export const fetchChildrenSuccess = createAction('FETCH_CHILDREN_SUCCESS', (id, json) => ({ id, json }));

export const fetchChildrenStart = createAction('FETCH_CHILDREN_START');

/**
 * Gets the children of a node from the API.
 */
export function fetchChildren(id = 'root') {
  return (dispatch, getState) => {
    const { explorer } = getState();

    dispatch(fetchChildrenStart(id));

    return admin.getChildPages(id, {
      fields: explorer.fields,
      filter: explorer.filter,
    }).then(json => dispatch(fetchChildrenSuccess(id, json)));
  };
}

// Make this a bit better... hmm....
export function fetchTree(id = 1) {
  return (dispatch) => {
    dispatch(fetchBranchStart(id));

    return admin.getPage(id).then((json) => {
      dispatch(fetchBranchSuccess(id, json));

      // Recursively walk up the tree to the root, to figure out how deep
      // in the tree we are.
      if (json.meta.parent) {
        dispatch(fetchTree(json.meta.parent.id));
      } else {
        dispatch(treeResolved());
      }
    });
  };
}

export function fetchRoot() {
  return (dispatch) => {
    // TODO Should not need an id.
    dispatch(resetTree(PAGES_ROOT_ID));
    dispatch(fetchBranchStart(PAGES_ROOT_ID));

    dispatch(fetchBranchSuccess(PAGES_ROOT_ID, {
      children: {},
      meta: {
        children: {},
      },
    }));

    dispatch(fetchChildren(PAGES_ROOT_ID));

    dispatch(treeResolved());
  };
}

export const toggleExplorer = createAction('TOGGLE_EXPLORER');


export function setFilter(filter) {
  return (dispatch, getState) => {
    const { explorer } = getState();
    const id = explorer.path[explorer.path.length - 1];

    dispatch({
      payload: {
        filter,
        id,
      },
      type: 'SET_FILTER',
    });

    dispatch(fetchChildren(id));
  };
}

/**
 * TODO: determine if page is already loaded, don't load it again, just push.
 */
export function fetchPage(id = 1) {
  return dispatch => {
    dispatch(fetchStart(id));
    return admin.getPage(id)
      .then(json => dispatch(fetchSuccess(id, json)))
      .then(json => dispatch(fetchChildren(id, json)))
      .catch(json => dispatch(fetchFailure(new Error(JSON.stringify(json)))));
  };
}

export const setDefaultPage = createAction('SET_DEFAULT_PAGE');
