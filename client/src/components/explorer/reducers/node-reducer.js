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

    case 'FETCH_CHILDREN_COMPLETE':
      return Object.assign({}, state, {
        items: action.json.items.map(item => { return item.id }),
        count: action.json.meta.total_count,
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
        [action.id]: Object.assign({}, state[action.id], {
          isFetching: true,
          children: children(state[action.id] ? state[action.id].children : undefined, action)
        })
      });

    case 'FETCH_CHILDREN_COMPLETE':
      let map = {};

      action.json.items.forEach(item => {
        map = Object.assign({}, map, {
          [item.id]: Object.assign({}, defaults, state[item.id], item, {
            isLoaded: true
          })
        });
      });

      return Object.assign({}, state, map, {
        [action.id]: Object.assign({}, state[action.id], {
          isFetching: false,
          children: children(state[action.id].children, action)
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
        [action.id]: Object.assign({}, defaults, state[action.id], {
          isFetching: true,
          isError: false,
        })
      });

    case 'FETCH_BRANCH_COMPLETE':
      return Object.assign({}, state, {
        [action.id]: Object.assign({}, defaults, state[action.id], action.json, {
          isFetching: false,
          isError: false,
          isLoaded: true
        })
      });

    case 'FETCH_COMPLETE':
      return state;
  }

  return state;
}
