import _ from 'lodash';

const childrenDefaultState = {
  items: [],
  count: 0,
  isFetching: false
};

const children = (state = childrenDefaultState, action) => {
  switch (action.type) {
  case 'FETCH_CHILDREN_START':
    return _.assign({}, state, {
      isFetching: true,
    });

  case 'FETCH_CHILDREN_SUCCESS':
    return _.assign({}, state, {
      items: action.payload.json.items.map(item => item.id),
      count: action.payload.json.meta.total_count,
      isFetching: false,
      isLoaded: true,
    });

  default:
    return state;
  }
};

const defaultState = {
  isError: false,
  isFetching: false,
  isLoaded: false,
  children: children(undefined, {})
};

// TODO Why isn't the default state used on init?
export default function nodes(state = {}, action) {
  switch (action.type) {
  case 'FETCH_CHILDREN_START':
    // TODO Very hard to understand this code. To refactor.
    return _.assign({}, state, {
      [action.payload]: _.assign({}, state[action.payload], {
        isFetching: true,
        children: children(state[action.payload] ? state[action.payload].children : undefined, action)
      })
    });

  // eslint-disable-next-line no-case-declarations
  case 'FETCH_CHILDREN_SUCCESS':
    // TODO Very hard to understand this code. To refactor.
    let map = {};
    action.payload.json.items.forEach(item => {
      map = _.assign({}, map, {
        [item.id]: _.assign({}, defaultState, state[item.id], item, {
          isLoaded: true
        })
      });
    });

    return _.assign({}, state, map, {
      [action.payload.id]: _.assign({}, state[action.payload.id], {
        isFetching: false,
        children: children(state[action.payload.id].children, action)
      })
    });

  case 'RESET_TREE':
    return defaultState;

  // eslint-disable-next-line no-case-declarations
  case 'SET_FILTER':
      // Unset all isLoaded states when the filter changes
    const updatedState = {};

    // TODO Do not use for in.
    // TODO Very hard to understand this code. To refactor.
    // eslint-disable-next-line
    for (let key in state) {
      if (state.hasOwnProperty(key)) {
        // eslint-disable-next-line prefer-const
        let obj = state[key];
        obj.children.isLoaded = false;
        updatedState[obj.id] = _.assign({}, obj, {
          isLoaded: false,
        });
      }
    }

    return _.assign({}, updatedState);

  case 'FETCH_START':
    return _.assign({}, state, {
      [action.payload]: _.assign({}, defaultState, state[action.payload], {
        isFetching: true,
        isError: false,
      })
    });

  case 'FETCH_BRANCH_SUCCESS':
    return _.assign({}, state, {
      [action.payload.id]: _.assign({}, defaultState, state[action.payload.id], action.payload.json, {
        isFetching: false,
        isError: false,
        isLoaded: true
      })
    });

  case 'FETCH_SUCCESS':
    return state;

  default:
    return state;
  }
}
