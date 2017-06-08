const defaultPageState = {
  isFetching: false,
  isError: false,
  children: {
    items: [],
    count: 0,
  },
  meta: {
    children: {},
  },
};

/**
 * A single page node in the explorer.
 */
const node = (state = defaultPageState, { type, payload }) => {
  switch (type) {
  case 'OPEN_EXPLORER':
    return state || defaultPageState;

  case 'GET_PAGE_SUCCESS':
    return Object.assign({}, state, payload.data, {
      isError: false,
    });

  case 'GET_CHILDREN_START':
    return Object.assign({}, state, {
      isFetching: true,
    });

  case 'GET_CHILDREN_SUCCESS':
    return Object.assign({}, state, {
      isFetching: false,
      isError: false,
      children: {
        items: state.children.items.slice().concat(payload.items.map(item => item.id)),
        count: payload.meta.total_count,
      },
    });

  case 'GET_PAGE_FAILURE':
  case 'GET_CHILDREN_FAILURE':
    return Object.assign({}, state, {
      isFetching: false,
      isError: true,
    });

  default:
    return state;
  }
};

const defaultState = {};

/**
 * Contains all of the page nodes in one object.
 */
export default function nodes(state = defaultState, { type, payload }) {
  switch (type) {

  case 'OPEN_EXPLORER':
  case 'GET_PAGE_SUCCESS':
  case 'GET_CHILDREN_START':
  case 'GET_PAGE_FAILURE':
  case 'GET_CHILDREN_FAILURE':
    return Object.assign({}, state, {
      // Delegate logic to single-node reducer.
      [payload.id]: node(state[payload.id], { type, payload }),
    });

  // eslint-disable-next-line no-case-declarations
  case 'GET_CHILDREN_SUCCESS':
    const newState = Object.assign({}, state, {
      [payload.id]: node(state[payload.id], { type, payload }),
    });

    payload.items.forEach((item) => {
      newState[item.id] = Object.assign({}, defaultPageState, item);
    });

    return newState;

  default:
    return state;
  }
}
