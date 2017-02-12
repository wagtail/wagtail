const defaultState = {};

const defaultPageState = {
  isFetching: false,
  isLoaded: true,
  isError: false,
  children: {
    items: [],
    count: 0,
    isFetching: false,
  },
  meta: {
    children: {},
  },
};

export default function nodes(prevState = defaultState, { type, payload }) {
  const state = Object.assign({}, prevState);

  switch (type) {
  case 'OPEN_EXPLORER':
    state[payload.id] = Object.assign({}, defaultPageState, state[payload.id]);
    break;

  case 'GET_PAGE_SUCCESS':
    state[payload.id] = Object.assign({}, state[payload.id], payload.data);
    state[payload.id].isError = false;
    break;

  case 'GET_CHILDREN_START':
    state[payload.id] = Object.assign({}, state[payload.id]);
    state[payload.id].isFetching = true;
    state[payload.id].children = Object.assign({}, state[payload.id].children);
    state[payload.id].children.isFetching = true;
    break;

  case 'GET_CHILDREN_SUCCESS':
    state[payload.id] = Object.assign({}, state[payload.id]);
    state[payload.id].isFetching = false;
    state[payload.id].isError = false;
    state[payload.id].children = Object.assign({}, state[payload.id].children, {
      items: state[payload.id].children.items.slice(),
      count: payload.meta.total_count,
      isFetching: false,
      isLoaded: true,
      isError: false,
    });

    payload.items.forEach((item) => {
      state[item.id] = Object.assign({}, defaultPageState, state[item.id], item);

      state[payload.id].children.items.push(item.id);
    });
    break;

  case 'GET_PAGE_FAILURE':
  case 'GET_CHILDREN_FAILURE':
    state[payload.id] = Object.assign({}, state[payload.id]);
    state[payload.id].isFetching = false;
    state[payload.id].isError = true;
    state[payload.id].children.isFetching = false;
    break;

  default:
    break;
  }

  return state;
}
