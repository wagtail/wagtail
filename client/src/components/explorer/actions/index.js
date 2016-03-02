import { API } from 'config';


export function fetchStart(id) {
  return {
    type: 'FETCH_START',
    id
  };
}

export function fetchComplete(id, body) {
  return {
    type: 'FETCH_COMPLETE',
    id,
    body
  };
}

export function fetchError(id, body) {
  return {
    type: 'FETCH_ERROR',
    id,
    body
  }
}

export function pushPage(id) {
  return {
    type: 'PUSH_PAGE',
    id: id,
  }
}

export function popPage(id)  {
  return {
    type: 'POP_PAGE',
    id: id,
  }
}


export function jsonHeaders() {
  let reqHeaders = new Headers();
  reqHeaders.append('Content-Type', 'application/json');

  return {
    method: 'GET',
    headers: reqHeaders,
    credentials: 'same-origin'
  };
}


export function fetchBranchComplete(id, json) {
  return {
    type: 'FETCH_BRANCH_COMPLETE',
    id,
    json
  }
}

export function fetchBranchStart(id) {
  return {
    type: 'FETCH_BRANCH_START',
    id
  }
}

export function clearError() {
  return {
    type: 'CLEAR_TRANSPORT_ERROR'
  }
}

export function resetTree(id) {
  return {
    type: 'RESET_TREE',
    id
  }
}

function _get(url) {
  return fetch(url, jsonHeaders()).then(response => response.json())
}


function treeResolved() {
  return {
    type: 'TREE_RESOLVED'
  }
}

// Make this a bit better... hmm....
export function fetchTree(id=1) {
  return dispatch => {
    dispatch(fetchBranchStart(id));

    return _get(`${API}/pages/${id}/`)
      .then(json => {
        dispatch(fetchBranchComplete(id, json))

        // Recursively walk up the tree to the root, to figure out how deep
        // in the tree we are.
        if (json.meta.parent) {
          dispatch(fetchTree(json.meta.parent.id));
        } else {
          dispatch(treeResolved())
        }
      });
  }
}

export function toggleExplorer() {
  return { type: 'TOGGLE_EXPLORER' };
}

export function setFilter(filter) {
  return (dispatch, getState) => {
    const { explorer } = getState();
    let id = explorer.react.path[explorer.react.path.length-1];

    dispatch({
      type: 'SET_FILTER',
      filter,
      id,
    });

    dispatch(fetchChildren(id))
  }
}

export function fetchChildrenComplete(id, json) {
  return {
    type: 'FETCH_CHILDREN_COMPLETE',
    id,
    json
  }
}

export function fetchChildrenStart(id) {
  return {
    type: 'FETCH_CHILDREN_START',
    id
  }
}


/**
 * Gets the children of a node from the API
 */
export function fetchChildren(id='root') {
  return (dispatch, getState) => {
    const { explorer } = getState();

    let api = `${API}/pages/?child_of=${id}`;

    if (explorer.react.filter) {
      api = `${api}&${explorer.react.filter}`
    }

    dispatch(fetchChildrenStart(id))
      return _get(api)
        .then(json => dispatch(fetchChildrenComplete(id, json)))
  }
}


/**
 * TODO: determine if page is already loaded, don't load it again, just push.
 */
export function fetchPage(id=1) {
  return dispatch => {
    dispatch(fetchStart(id))
    return _get(`${API}/pages/${id}/`)
      .then(json => dispatch(fetchComplete(id, json)))
      .then(json => dispatch(fetchChildren(id, json)))
      .catch(json => dispatch(fetchError(id, json)))
  }
}


export function setDefaultPage(id) {
  return {
    type: 'SET_DEFAULT_PAGE',
    id
  }
}
