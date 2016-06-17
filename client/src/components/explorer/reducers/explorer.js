const stateDefaults = {
  isVisible: false,
  isFetching: false,
  isResolved: false,
  path: [],
  currentPage: 1,
  defaultPage: 1,
  // Specificies which fields are to be fetched in the API calls.
  fields: ['title', 'latest_revision_created_at', 'status', 'descendants', 'children'],
  filter: 'has_children=1',
}

export default function explorer(state = stateDefaults, action) {

  let newNodes = state.path;

  switch (action.type) {
    case 'SET_DEFAULT_PAGE':
      return Object.assign({}, state, {
        defaultPage: action.id
      });

    case 'RESET_TREE':
      return Object.assign({}, state, {
        isFetching: true,
        isResolved: false,
        currentPage: action.id,
        path: [],
      });

    case 'TREE_RESOLVED':
      return Object.assign({}, state, {
        isFetching: false,
        isResolved: true
      });

    case 'TOGGLE_EXPLORER':
      return Object.assign({}, state, {
        isVisible: !state.isVisible,
        currentPage: action.id ? action.id : state.defaultPage,
      });

    case 'FETCH_START':
      return Object.assign({}, state, {
        isFetching: true
      });

    case 'FETCH_BRANCH_COMPLETE':
      if (state.path.indexOf(action.id) < 0) {
        newNodes = [action.id].concat(state.path);
      }

      return Object.assign({}, state, {
        path: newNodes,
        currentPage: state.currentPage ? state.currentPage : action.id
      });

    // called on fetch page...
    case 'FETCH_COMPLETE':
      if (state.path.indexOf(action.id) < 0) {
        newNodes = state.path.concat([action.id]);
      }

      return Object.assign({}, state, {
        isFetching: false,
        path: newNodes,
      });

    case 'PUSH_PAGE':
      return Object.assign({}, state, {
        path: state.path.concat([action.id])
      });
      return state;

    case 'POP_PAGE':
      let poppedNodes = state.path.length > 1 ? state.path.slice(0, -1) : state.path;
      return Object.assign({}, state, {
        path: poppedNodes,
      });

    case 'FETCH_CHILDREN_COMPLETE':
      return Object.assign({}, state, {
        isFetching: false,
      });

    case 'SET_FILTER':
      return Object.assign({}, state, {
        filter: action.filter
      });
  }
  return state;
}
