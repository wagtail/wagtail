export default function transport(state={error: null, showMessage: false}, action) {
  switch(action.type) {
    case 'FETCH_FAILURE':
      return Object.assign({}, state, {
        error: action.payload.message,
        showMessage: true
      });
    case 'CLEAR_TRANSPORT_ERROR':
      return Object.assign({}, state, {
        error: null,
        showMessage: false
      });
  }
  return state;
}
