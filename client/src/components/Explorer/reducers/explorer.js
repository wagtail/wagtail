const defaultState = {
  api: null,
  isVisible: false,
  path: [],
};

/**
 * Oversees the state of the explorer. Defines:
 * - Where in the page tree the explorer is at.
 * - Whether the explorer is open or not.
 */
export default function explorer(prevState = defaultState, { type, payload }) {
  switch (type) {
  case 'SET_API':
    return Object.assign({}, prevState, {
      api: payload.api,
    });

  case 'OPEN_EXPLORER':
    // Provide a starting page when opening the explorer.
    return {
      api: prevState.api,
      isVisible: true,
      path: [payload.id],
    };

  case 'CLOSE_EXPLORER':
    return Object.assign({}, defaultState, {
      api: prevState.api,
    });

  case 'PUSH_PAGE':
    return {
      api: prevState.api,
      isVisible: prevState.isVisible,
      path: prevState.path.concat([payload.id]),
    };

  case 'POP_PAGE':
    return {
      api: prevState.api,
      isVisible: prevState.isVisible,
      path: prevState.path.slice(0, -1),
    };

  default:
    return prevState;
  }
}
