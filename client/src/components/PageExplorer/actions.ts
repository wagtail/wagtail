import { ThunkAction } from 'redux-thunk';

import * as admin from '../../api/admin';
import { createAction } from '../../utils/actions';
import { MAX_EXPLORER_PAGES } from '../../config/wagtailConfig';

import { State, Action } from './reducers';

type ThunkActionType = ThunkAction<void, State, unknown, Action>;

const getPageSuccess = createAction(
  'GET_PAGE_SUCCESS',
  (id: number, data: admin.WagtailPageAPI) => ({ id, data }),
);
const getPageFailure = createAction(
  'GET_PAGE_FAILURE',
  (id: number, error: Error) => ({ id, error }),
);

/**
 * Gets a page from the API.
 */
function getPage(id: number): ThunkActionType {
  return (dispatch) =>
    admin.getPage(id).then(
      (data) => {
        dispatch(getPageSuccess(id, data));
      },
      (error) => {
        dispatch(getPageFailure(id, error));
      },
    );
}

const getChildrenStart = createAction('GET_CHILDREN_START', (id: number) => ({
  id,
}));
const getChildrenSuccess = createAction(
  'GET_CHILDREN_SUCCESS',
  (id, items: admin.WagtailPageAPI[], meta: any) => ({ id, items, meta }),
);
const getChildrenFailure = createAction(
  'GET_CHILDREN_FAILURE',
  (id: number, error: Error) => ({ id, error }),
);

/**
 * Gets the children of a node from the API.
 */
function getChildren(id: number, offset = 0): ThunkActionType {
  return (dispatch) => {
    dispatch(getChildrenStart(id));

    return admin
      .getPageChildren(id, {
        offset: offset,
      })
      .then(
        ({ items, meta }) => {
          const nbPages = offset + items.length;
          dispatch(getChildrenSuccess(id, items, meta));

          // Load more pages if necessary. Only one request is created even though
          // more might be needed, thus naturally throttling the loading.
          if (nbPages < meta.total_count && nbPages < MAX_EXPLORER_PAGES) {
            dispatch(getChildren(id, nbPages));
          }
        },
        (error) => {
          dispatch(getChildrenFailure(id, error));
        },
      );
  };
}

const getTranslationsStart = createAction('GET_TRANSLATIONS_START', (id) => ({
  id,
}));
const getTranslationsSuccess = createAction(
  'GET_TRANSLATIONS_SUCCESS',
  (id, items) => ({ id, items }),
);
const getTranslationsFailure = createAction(
  'GET_TRANSLATIONS_FAILURE',
  (id, error) => ({ id, error }),
);

/**
 * Gets the translations of a node from the API.
 */
function getTranslations(id) {
  return (dispatch) => {
    dispatch(getTranslationsStart(id));

    return admin.getAllPageTranslations(id, { onlyWithChildren: true }).then(
      (items) => {
        dispatch(getTranslationsSuccess(id, items));
      },
      (error) => {
        dispatch(getTranslationsFailure(id, error));
      },
    );
  };
}

const openPageExplorerPrivate = createAction('OPEN_EXPLORER', (id) => ({ id }));
export const closePageExplorer = createAction('CLOSE_EXPLORER');

export function openPageExplorer(id: number): ThunkActionType {
  return (dispatch, getState) => {
    const { nodes } = getState();

    const page = nodes[id];

    dispatch(openPageExplorerPrivate(id));

    if (!page) {
      dispatch(getChildren(id));

      if (id !== 1) {
        dispatch(getTranslations(id));
      }
    }

    // We need to get the title of the starting page, only if it is not the site's root.
    const isNotRoot = id !== 1;
    if (isNotRoot) {
      dispatch(getPage(id));
    }
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

    dispatch(gotoPagePrivate(id, transition));

    if (page && !page.isFetchingChildren && !(page.children.count > 0)) {
      dispatch(getChildren(id));
    }

    if (page && !page.isFetchingTranslations && page.translations == null) {
      dispatch(getTranslations(id));
    }
  };
}
