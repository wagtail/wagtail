const defaultState = {
  isVisible: false,
  depth: 0,
  page: null,
};

/**
 * Oversees the state of the explorer. Defines:
 * - Where in the page tree the explorer is at.
 * - Whether the explorer is open or not.
 */
export default function explorer(prevState = defaultState, { type, payload }) {
  switch (type) {
  case 'OPEN_EXPLORER':
    // Provide a starting page when opening the explorer.
    return {
      isVisible: true,
      depth: 0,
      page: payload.id,
    };

  case 'CLOSE_EXPLORER':
    return defaultState;

  case 'GOTO_PAGE':
    return {
      isVisible: prevState.isVisible,
      depth: prevState.depth + payload.transition,
      page: payload.id,
    };

  default:
    return prevState;
  }
}
