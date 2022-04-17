export interface State {
  depth: number;
  currentPageId: number | null;
}

const defaultState: State = {
  depth: 0,
  currentPageId: null,
};

export const OPEN_EXPLORER = 'OPEN_EXPLORER';
interface OpenPageExplorerAction {
  type: typeof OPEN_EXPLORER;
  payload: {
    id: number;
  };
}

export const CLOSE_EXPLORER = 'CLOSE_EXPLORER';
interface ClosePageExplorerAction {
  type: typeof CLOSE_EXPLORER;
}

export const GOTO_PAGE = 'GOTO_PAGE';
interface GotoPageAction {
  type: typeof GOTO_PAGE;
  payload: {
    id: number;
    transition: number;
  };
}

export type Action =
  | OpenPageExplorerAction
  | ClosePageExplorerAction
  | GotoPageAction;

/**
 * Oversees the state of the explorer. Defines:
 * - Where in the page tree the explorer is at.
 * - Whether the explorer is open or not.
 */
export default function explorer(
  prevState = defaultState,
  action: Action,
): State {
  switch (action.type) {
    case OPEN_EXPLORER:
      // Provide a starting page when opening the explorer.
      return {
        depth: 0,
        currentPageId: action.payload.id,
      };

    case CLOSE_EXPLORER:
      return defaultState;

    case GOTO_PAGE:
      return {
        depth: prevState.depth + action.payload.transition,
        currentPageId: action.payload.id,
      };

    default:
      return prevState;
  }
}
