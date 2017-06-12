const defaultState = {
  isFetching: false,
  error: null,
  parent: null,
  items: [],
  totalItems: 0,
  pageTypes: {},
  viewName: 'browse',
  viewOptions: {
    parentPageID: 'root',
    pageNumber: 1,
  },
};

export default function pageChooser(state = defaultState, { type, payload }) {
  switch (type) {
  case 'SET_VIEW':
    return Object.assign({}, state, {
      viewName: payload.viewName,
      viewOptions: payload.viewOptions,
    });

  case 'FETCH_START':
    return Object.assign({}, state, {
      isFetching: true,
      error: null,
    });

  case 'FETCH_SUCCESS':
    return Object.assign({}, state, {
      isFetching: false,
      parent: payload.parentJson,
      items: payload.itemsJson.items,
      totalItems: payload.itemsJson.meta.total_count,
      // eslint-disable-next-line no-underscore-dangle
      pageTypes: Object.assign({}, state.pageTypes, payload.itemsJson.__types),
    });

  case 'FETCH_FAILURE':
    return Object.assign({}, state, {
      isFetching: false,
      error: payload.message,
      items: [],
      totalItems: 0,
    });

  default:
    return state;
  }
}
