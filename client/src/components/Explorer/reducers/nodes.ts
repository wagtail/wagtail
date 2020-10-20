import { WagtailPageAPI } from '../../../api/admin';
import { OPEN_EXPLORER } from './explorer';

export interface PageState extends WagtailPageAPI {
  isFetching: boolean;
  isError: boolean;
  children: {
    items: any[];
    count: number;
  };
}

const defaultPageState: PageState = {
  id: 0,
  isFetching: false,
  isError: false,
  children: {
    items: [],
    count: 0,
  },
  meta: {
    status: {
      status: '',
      live: false,
      has_unpublished_changes: true
    },
    children: {},
  },
};

interface OpenExplorerAction {
  type: typeof OPEN_EXPLORER;
  payload: {
    id: number;
  }
}

export const GET_PAGE_SUCCESS = 'GET_PAGE_SUCCESS';
interface GetPageSuccess {
  type: typeof GET_PAGE_SUCCESS;
  payload: {
    id: number;
    data: WagtailPageAPI;
  };
}

export const GET_CHILDREN_START = 'GET_CHILDREN_START';
interface GetChildrenStart {
  type: typeof GET_CHILDREN_START;
  payload: {
    id: number;
  };
}

export const GET_CHILDREN_SUCCESS = 'GET_CHILDREN_SUCCESS';
interface GetChildrenSuccess {
  type: typeof GET_CHILDREN_SUCCESS;
  payload: {
    id: number;
    meta: {
      /* eslint-disable-next-line camelcase */
      total_count: number;
    };
    items: WagtailPageAPI[];
  };
}

export const GET_PAGE_FAILURE = 'GET_PAGE_FAILURE';
interface GetPageFailure {
  type: typeof GET_PAGE_FAILURE;
  payload: {
    id: number;
  };
}

export const GET_CHILDREN_FAILURE = 'GET_CHILDREN_FAILURE';
interface GetChildrenFailure {
  type: typeof GET_CHILDREN_FAILURE;
  payload: {
    id: number;
  };
}

export type Action = OpenExplorerAction
                   | GetPageSuccess
                   | GetChildrenStart
                   | GetChildrenSuccess
                   | GetPageFailure
                   | GetChildrenFailure;

/**
 * A single page node in the explorer.
 */
const node = (state = defaultPageState, action: Action) => {
  switch (action.type) {
  case OPEN_EXPLORER:
    return state || defaultPageState;

  case GET_PAGE_SUCCESS:
    return Object.assign({}, state, action.payload.data, {
      isError: false,
    });

  case GET_CHILDREN_START:
    return Object.assign({}, state, {
      isFetching: true,
    });

  case GET_CHILDREN_SUCCESS:
    return Object.assign({}, state, {
      isFetching: false,
      isError: false,
      children: {
        items: state.children.items.slice().concat(action.payload.items.map(item => item.id)),
        count: action.payload.meta.total_count,
      },
    });

  case GET_PAGE_FAILURE:
  case GET_CHILDREN_FAILURE:
    return Object.assign({}, state, {
      isFetching: false,
      isError: true,
    });

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
export default function nodes(state = defaultState, action: Action) {
  switch (action.type) {
  case OPEN_EXPLORER:
  case GET_PAGE_SUCCESS:
  case GET_CHILDREN_START:
  case GET_PAGE_FAILURE:
  case GET_CHILDREN_FAILURE:
    return Object.assign({}, state, {
      // Delegate logic to single-node reducer.
      [action.payload.id]: node(state[action.payload.id], action),
    });

  case 'GET_CHILDREN_SUCCESS':
    // eslint-disable-next-line no-case-declarations
    const newState = Object.assign({}, state, {
      [action.payload.id]: node(state[action.payload.id], action),
    });

    action.payload.items.forEach((item) => {
      newState[item.id] = Object.assign({}, defaultPageState, item);
    });

    return newState;

  default:
    return state;
  }
}
