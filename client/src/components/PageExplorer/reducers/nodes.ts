import { WagtailPageAPI } from '../../../api/admin';
import { OPEN_EXPLORER, CLOSE_EXPLORER } from './explorer';

export interface PageState extends WagtailPageAPI {
  isFetchingChildren: boolean;
  isFetchingTranslations: boolean;
  isError: boolean;
  children: {
    items: any[];
    count: number;
  };
  translations?: Map<string, number>;
}

const defaultPageState: PageState = {
  id: 0,
  isFetchingChildren: false,
  isFetchingTranslations: false,
  isError: false,
  children: {
    items: [],
    count: 0,
  },
  meta: {
    status: {
      status: '',
      live: false,
      has_unpublished_changes: true,
    },
    parent: null,
    children: {},
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
      total_count: number;
    };
    items: WagtailPageAPI[];
  };
}

export const GET_TRANSLATIONS_START = 'GET_TRANSLATIONS_START';
interface GetTranslationsStart {
  type: typeof GET_TRANSLATIONS_START;
  payload: {
    id: number;
  };
}

export const GET_TRANSLATIONS_SUCCESS = 'GET_TRANSLATIONS_SUCCESS';
interface GetTranslationsSuccess {
  type: typeof GET_TRANSLATIONS_SUCCESS;
  payload: {
    id: number;
    meta: {
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

export const GET_TRANSLATIONS_FAILURE = 'GET_TRANSLATIONS_FAILURE';
interface GetTranslationsFailure {
  type: typeof GET_TRANSLATIONS_FAILURE;
  payload: {
    id: number;
  };
}

export type Action =
  | OpenPageExplorerAction
  | ClosePageExplorerAction
  | GetPageSuccess
  | GetChildrenStart
  | GetChildrenSuccess
  | GetTranslationsStart
  | GetTranslationsSuccess
  | GetPageFailure
  | GetChildrenFailure
  | GetTranslationsFailure;

/**
 * A single page node in the explorer.
 */
const node = (state = defaultPageState, action: Action): PageState => {
  switch (action.type) {
    case GET_PAGE_SUCCESS:
      return { ...state, ...action.payload.data, isError: false };

    case GET_CHILDREN_START:
      return { ...state, isFetchingChildren: true };

    case GET_TRANSLATIONS_START:
      return { ...state, isFetchingTranslations: true };

    case GET_CHILDREN_SUCCESS:
      return {
        ...state,
        isFetchingChildren: false,
        isError: false,
        children: {
          items: state.children.items
            .slice()
            .concat(action.payload.items.map((item) => item.id)),
          count: action.payload.meta.total_count,
        },
      };

    case GET_TRANSLATIONS_SUCCESS:
      // eslint-disable-next-line no-case-declarations
      const translations = new Map();

      action.payload.items.forEach((item) => {
        translations.set(item.meta.locale, item.id);
      });

      return {
        ...state,
        isFetchingTranslations: false,
        isError: false,
        translations,
      };

    case GET_PAGE_FAILURE:
    case GET_CHILDREN_FAILURE:
    case GET_TRANSLATIONS_FAILURE:
      return {
        ...state,
        isFetchingChildren: false,
        isFetchingTranslations: true,
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
export default function nodes(state = defaultState, action: Action) {
  switch (action.type) {
    case OPEN_EXPLORER: {
      return { ...state, [action.payload.id]: { ...defaultPageState } };
    }

    case GET_PAGE_SUCCESS:
    case GET_CHILDREN_START:
    case GET_TRANSLATIONS_START:
    case GET_PAGE_FAILURE:
    case GET_CHILDREN_FAILURE:
    case GET_TRANSLATIONS_FAILURE:
      return {
        ...state, // Delegate logic to single-node reducer.
        [action.payload.id]: node(state[action.payload.id], action),
      };

    case GET_CHILDREN_SUCCESS:
    case GET_TRANSLATIONS_SUCCESS:
      // eslint-disable-next-line no-case-declarations
      const newState = {
        ...state,
        [action.payload.id]: node(state[action.payload.id], action),
      };

      action.payload.items.forEach((item) => {
        newState[item.id] = { ...defaultPageState, ...item };
      });

      return newState;

    case CLOSE_EXPLORER: {
      return defaultState;
    }

    default:
      return state;
  }
}
