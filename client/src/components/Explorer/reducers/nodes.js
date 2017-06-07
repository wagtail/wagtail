const defaultState = {};

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

export default function nodes(prevState = defaultState, { type, payload }) {
  let state = prevState;

  switch (type) {
  case 'OPEN_EXPLORER':
    state = Object.assign({}, prevState);
    state[payload.id] = Object.assign({}, defaultPageState, state[payload.id]);
    return state;

  case 'GET_PAGE_SUCCESS':
    state = Object.assign({}, prevState);
    state[payload.id] = Object.assign({}, state[payload.id], payload.data);
    state[payload.id].isError = false;
    return state;

  case 'GET_CHILDREN_START':
    state = Object.assign({}, prevState);
    state[payload.id] = Object.assign({}, state[payload.id]);
    state[payload.id].isFetching = true;
    state[payload.id].children = Object.assign({}, state[payload.id].children);
    return state;

  case 'GET_CHILDREN_SUCCESS':
    state = Object.assign({}, prevState);
    state[payload.id] = Object.assign({}, state[payload.id]);
    state[payload.id].isFetching = false;
    state[payload.id].isError = false;
    state[payload.id].children = Object.assign({}, state[payload.id].children, {
      items: state[payload.id].children.items.slice(),
      count: payload.meta.total_count,
    });

    payload.items.forEach((item) => {
      state[item.id] = Object.assign({}, defaultPageState, state[item.id], item);

      state[payload.id].children.items.push(item.id);
    });
    return state;

  case 'GET_PAGE_FAILURE':
  case 'GET_CHILDREN_FAILURE':
    state = Object.assign({}, prevState);
    state[payload.id] = Object.assign({}, state[payload.id]);
    state[payload.id].isFetching = false;
    state[payload.id].isError = true;
    return state;

  default:
    return state;
  }
}
