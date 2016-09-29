import _ from 'lodash';


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
  }
};


export default function pageChooser(state = defaultState, action) {
  switch (action.type) {
    case 'SET_VIEW':
      return _.assign({}, state, {
        viewName: action.payload.viewName,
        viewOptions: action.payload.viewOptions,
      });

    case 'FETCH_START':
      return _.assign({}, state, {
        isFetching: true,
        error: null,
      });

    case 'FETCH_SUCCESS':
      return _.assign({}, state, {
        isFetching: false,
        parent: action.payload.parentJson,
        items: action.payload.itemsJson.items,
        totalItems: action.payload.itemsJson.meta.total_count,
        pageTypes: _.assign({}, state.pageTypes, action.payload.itemsJson.__types),
      });

    case 'FETCH_FAILURE':
      return _.assign({}, state, {
        isFetching: false,
        error: action.payload.message,
        items: [],
        totalItems: 0,
      });

    default:
      return state;
  }
}
