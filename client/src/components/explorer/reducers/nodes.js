function children(state={
  items: [],
  count: 0,
  isFetching: false
}, action) {

  switch(action.type) {
    case 'FETCH_CHILDREN_START':
      return Object.assign({}, state, {
        isFetching: true
      });

    case 'FETCH_CHILDREN_SUCCESS':
      return Object.assign({}, state, {
        items: action.payload.json.items.map(item => { return item.id }),
        count: action.payload.json.meta.total_count,
        isFetching: false,
        isLoaded: true
      });
  }
  return state;
}


export default function nodes(state = {}, action) {
  let defaults = {
    isError: false,
    isFetching: false,
    isLoaded: false,
    children: children(undefined, {})
  };

  switch(action.type) {
    case 'FETCH_CHILDREN_START':
      return Object.assign({}, state, {
        [action.payload]: Object.assign({}, state[action.payload], {
          isFetching: true,
          children: children(state[action.payload] ? state[action.payload].children : undefined, action)
        })
      });

    case 'FETCH_CHILDREN_SUCCESS':
      let map = {};

      action.payload.json.items.forEach(item => {
        map = Object.assign({}, map, {
          [item.id]: Object.assign({}, defaults, state[item.id], item, {
            isLoaded: true
          })
        });
      });

      return Object.assign({}, state, map, {
        [action.payload.id]: Object.assign({}, state[action.payload.id], {
          isFetching: false,
          children: children(state[action.payload.id].children, action)
        })
      });

    case 'RESET_TREE':
      return Object.assign({}, {});

    case 'SET_FILTER':
      // Unset all isLoaded states when the filter changes
      let updatedState = {};

      for (let _key in state) {
        if (state.hasOwnProperty( _key )) {
          let _obj = state[_key];
          _obj.children.isLoaded = false;
          updatedState[_obj.id] = Object.assign({}, _obj, { isLoaded: false })
        }
      }

      return Object.assign({}, updatedState);

    case 'FETCH_START':
      return Object.assign({}, state, {
        [action.payload]: Object.assign({}, defaults, state[action.payload], {
          isFetching: true,
          isError: false,
        })
      });

    case 'FETCH_BRANCH_SUCCESS':
      return Object.assign({}, state, {
        [action.payload.id]: Object.assign({}, defaults, state[action.payload.id], action.payload.json, {
          isFetching: false,
          isError: false,
          isLoaded: true
        })
      });

    case 'FETCH_SUCCESS':
      return state;
  }

  return state;
}
