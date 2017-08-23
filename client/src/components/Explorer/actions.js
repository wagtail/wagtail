import * as admin from '../../api/admin';
import { createAction } from '../../utils/actions';
import { MAX_EXPLORER_PAGES } from '../../config/wagtailConfig';

const getPageStart = createAction('GET_PAGE_START');
const getPageSuccess = createAction('GET_PAGE_SUCCESS', (id, data) => ({ id, data }));
const getPageFailure = createAction('GET_PAGE_FAILURE', (id, error) => ({ id, error }));

/**
 * Gets a page from the API.
 */
function getPage(id) {
  return (dispatch) => {
    dispatch(getPageStart(id));

    return admin.getPage(id).then((data) => {
      dispatch(getPageSuccess(id, data));
    }, (error) => {
      dispatch(getPageFailure(id, error));
    });
  };
}

const getChildrenStart = createAction('GET_CHILDREN_START', id => ({ id }));
const getChildrenSuccess = createAction('GET_CHILDREN_SUCCESS', (id, items, meta) => ({ id, items, meta }));
const getChildrenFailure = createAction('GET_CHILDREN_FAILURE', (id, error) => ({ id, error }));

/**
 * Gets the children of a node from the API.
 */
function getChildren(id, offset = 0) {
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

export function toggleExplorer(id) {
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
const pushPagePrivate = createAction('PUSH_PAGE', id => ({ id }));

export function pushPage(id) {
  return (dispatch, getState) => {
    const { nodes } = getState();
    const page = nodes[id];

    dispatch(pushPagePrivate(id));

    if (page && !page.isFetching && !page.children.count > 0) {
      dispatch(getChildren(id));
    }
  };
}
