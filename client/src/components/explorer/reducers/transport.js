import _ from 'lodash';

const defaultState = {
  error: null,
  showMessage: false,
};

export default function transport(state = defaultState, action) {
  switch (action.type) {
  case 'FETCH_FAILURE':
    return _.assign({}, state, {
      error: action.payload.message,
      showMessage: true
    });
  case 'CLEAR_TRANSPORT_ERROR':
    return _.assign({}, state, {
      error: null,
      showMessage: false
    });
  default:
    return state;
  }
}
