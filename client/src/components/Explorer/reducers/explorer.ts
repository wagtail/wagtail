export interface State {
  isVisible: boolean;
  path: number[];
}

const defaultState: State = {
  isVisible: false,
  path: [],
};

export const OPEN_EXPLORER = 'OPEN_EXPLORER';
interface OpenExplorerAction {
  type: typeof OPEN_EXPLORER;
  payload: {
    id: number;
  }
}

export const CLOSE_EXPLORER = 'CLOSE_EXPLORER';
interface CloseExplorerAction {
  type: typeof CLOSE_EXPLORER;
}

export const PUSH_PAGE = 'PUSH_PAGE';
interface PushPageAction {
  type: typeof PUSH_PAGE;
  payload: {
    id: number;
  }
}

export const POP_PAGE = 'POP_PAGE';
interface PopPageAction {
  type: typeof POP_PAGE;
}

export type Action = OpenExplorerAction | CloseExplorerAction | PushPageAction | PopPageAction;

/**
 * Oversees the state of the explorer. Defines:
 * - Where in the page tree the explorer is at.
 * - Whether the explorer is open or not.
 */
export default function explorer(prevState = defaultState, action: Action) {
  switch (action.type) {
  case OPEN_EXPLORER:
    // Provide a starting page when opening the explorer.
    return {
      isVisible: true,
      path: [action.payload.id],
    };

  case CLOSE_EXPLORER:
    return defaultState;

  case PUSH_PAGE:
    return {
      isVisible: prevState.isVisible,
      path: prevState.path.concat([action.payload.id]),
    };

  case POP_PAGE:
    return {
      isVisible: prevState.isVisible,
      path: prevState.path.slice(0, -1),
    };

  default:
    return prevState;
  }
}
