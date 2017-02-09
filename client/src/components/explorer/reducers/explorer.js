import _ from 'lodash';

const defaultState = {
  isVisible: false,
  isFetching: false,
  isResolved: false,
  path: [],
  currentPage: 1,
  defaultPage: 1,
  // TODO Change to include less fields (just 'descendants'?) in the next version of the admin API.
  // Specificies which fields are to be fetched in the API calls.
  fields: ['title', 'latest_revision_created_at', 'status', 'descendants', 'children'],
  // Coming from the API in order to get translated / pluralised labels.
  pageTypes: {},
};

export default function explorer(state = defaultState, action = {}) {
  let newNodes = state.path;

  switch (action.type) {
  case 'SET_DEFAULT_PAGE':
    return _.assign({}, state, {
      defaultPage: action.payload
    });

  case 'RESET_TREE':
    return _.assign({}, state, {
      isFetching: true,
      isResolved: false,
      currentPage: action.payload,
      path: [],
    });

  case 'TREE_RESOLVED':
    return _.assign({}, state, {
      isFetching: false,
      isResolved: true
    });

  case 'TOGGLE_EXPLORER':
    return _.assign({}, state, {
      isVisible: !state.isVisible,
      currentPage: action.payload ? action.payload : state.defaultPage,
    });

  case 'FETCH_START':
    return _.assign({}, state, {
      isFetching: true
    });

  case 'FETCH_BRANCH_SUCCESS':
    if (state.path.indexOf(action.payload.id) < 0) {
      newNodes = [action.payload.id].concat(state.path);
    }

    return _.assign({}, state, {
      path: newNodes,
      currentPage: state.currentPage ? state.currentPage : action.payload.id
    });

    // called on fetch page...
  case 'FETCH_SUCCESS':
    if (state.path.indexOf(action.payload.id) < 0) {
      newNodes = state.path.concat([action.payload.id]);
    }

    return _.assign({}, state, {
      isFetching: false,
      path: newNodes,
    });

  case 'PUSH_PAGE':
    return _.assign({}, state, {
      path: state.path.concat([action.payload])
    });

  case 'POP_PAGE':
    return _.assign({}, state, {
      path: state.path.length > 1 ? state.path.slice(0, -1) : state.path,
    });

  case 'FETCH_CHILDREN_SUCCESS':
    return _.assign({}, state, {
      isFetching: false,
      // eslint-disable-next-line no-underscore-dangle
      pageTypes: _.assign({}, state.pageTypes, action.payload.json.__types),
    });

  default:
    return state;
  }
}
