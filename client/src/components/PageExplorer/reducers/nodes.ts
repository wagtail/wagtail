import { WagtailExplorerAPI, WagtailPageAPI } from '../../../api/admin';
import { CLOSE_EXPLORER, OPEN_EXPLORER } from './explorer';

export interface PageState extends WagtailPageAPI {
  isFetching: boolean;
  isLoaded: boolean;
  isError: boolean;
  children: {
    items: any[];
    count: number;
  };
  translations?: Map<string, number>;
}

const defaultPageState: PageState = {
  id: 0,
  title: '',
  admin_display_title: '',
  isFetching: false,
  isLoaded: false,
  isError: false,
  children: {
    items: [],
    count: 0,
  },
  meta: {
    type: '',
    locale: '',
    depth: 0,
    status: '',
    live: false,
    has_unpublished_changes: true,
    has_children: false,
  },
};

interface OpenPageExplorerAction {
  type: typeof OPEN_EXPLORER;
  payload: {
    id: number;
  };
}

interface ClosePageExplorerAction {
  type: typeof CLOSE_EXPLORER;
}

export const GET_PAGE_START = 'GET_PAGE_START';
interface GetPageStart {
  type: typeof GET_PAGE_START;
  payload: {
    id: number;
  };
}

export const GET_PAGE_SUCCESS = 'GET_PAGE_SUCCESS';
interface GetPageSuccess {
  type: typeof GET_PAGE_SUCCESS;
  payload: {
    id: number;
    data: WagtailExplorerAPI;
    offset: number;
  };
}

export const GET_PAGE_FAILURE = 'GET_PAGE_FAILURE';
interface GetPageFailure {
  type: typeof GET_PAGE_FAILURE;
  payload: {
    id: number;
  };
}

export type Action =
  | OpenPageExplorerAction
  | ClosePageExplorerAction
  | GetPageStart
  | GetPageSuccess
  | GetPageFailure;

/**
 * Whether a response for more children doesn't follow on from the children
 * already loaded, e.g. it belongs to a request made before the explorer was
 * closed and reopened.
 */
const isStaleChildrenPage = (
  state: PageState | undefined,
  offset: number,
): boolean => offset > 0 && offset !== state?.children.items.length;

/**
 * A single page node in the explorer.
 */
const node = (
  state = defaultPageState /* eslint-disable-line default-param-last */,
  action: Action,
): PageState => {
  switch (action.type) {
    case GET_PAGE_START:
      return { ...state, isFetching: true };

    case GET_PAGE_SUCCESS: {
      const { data, offset } = action.payload;
      const previousItems = offset > 0 ? state.children.items : [];

      return {
        ...state,
        ...data.page,
        isFetching: false,
        isLoaded: true,
        isError: false,
        children: {
          items: previousItems.concat(
            data.children.items.map((item) => item.id),
          ),
          count: data.children.count,
        },
        translations: new Map(
          data.translations.map((translation) => [
            translation.locale,
            translation.id,
          ]),
        ),
      };
    }

    case GET_PAGE_FAILURE:
      return {
        ...state,
        isFetching: false,
        isError: true,
      };

    default:
      return state;
  }
};

export interface State {
  [id: number]: PageState;
}

const defaultState: State = {};

/**
 * Contains all of the page nodes in one object.
 */
export default function nodes(
  state = defaultState /* eslint-disable-line default-param-last */,
  action: Action,
) {
  switch (action.type) {
    case OPEN_EXPLORER: {
      return { ...state, [action.payload.id]: { ...defaultPageState } };
    }

    case GET_PAGE_START:
    case GET_PAGE_FAILURE:
      return {
        ...state, // Delegate logic to single-node reducer.
        [action.payload.id]: node(state[action.payload.id], action),
      };

    case GET_PAGE_SUCCESS: {
      if (
        isStaleChildrenPage(state[action.payload.id], action.payload.offset)
      ) {
        return state;
      }

      const newState = { ...state };

      // Children are only partially known until they are loaded themselves.
      action.payload.data.children.items.forEach((item) => {
        newState[item.id] = { ...defaultPageState, ...item };
      });

      newState[action.payload.id] = node(state[action.payload.id], action);

      return newState;
    }

    case CLOSE_EXPLORER: {
      return defaultState;
    }

    default:
      return state;
  }
}
