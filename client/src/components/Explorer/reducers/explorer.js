const defaultState = {
  isVisible: false,
  path: [],
};

/**
 * Oversees the state of the explorer. Defines:
 * - Where in the page tree the explorer is at.
 * - Whether the explorer is open or not.
 */
export default function explorer(prevState = defaultState, { type, payload }) {
  const state = Object.assign({}, prevState);

  switch (type) {
  case 'OPEN_EXPLORER':
    // Provide a starting page when opening the explorer.
    state.path = [payload.id];
    state.isVisible = true;
    break;

  case 'CLOSE_EXPLORER':
    state.path = [];
    state.isVisible = false;
    break;

  case 'PUSH_PAGE':
    state.path = state.path.concat([payload.id]);
    break;

  case 'POP_PAGE':
    state.path = state.path.slice(0, -1);
    break;

  default:
    break;
  }

  return state;
}
