import nodes from './nodes';

const explorerResponse = {
  page: {
    id: 1,
    admin_display_title: 'Home',
    meta: {
      depth: 2,
      status: 'live',
      live: true,
      has_unpublished_changes: false,
      has_children: true,
      locale: 'en',
      parent: { id: 99, title: 'Root', meta: {} },
    },
  },
  translations: [
    { id: 7, locale: 'fr' },
    { id: 8, locale: 'de' },
  ],
  children: {
    count: 5,
    items: [
      { id: 3, admin_display_title: 'Three', meta: { depth: 3 } },
      { id: 4, admin_display_title: 'Four', meta: { depth: 3 } },
      { id: 5, admin_display_title: 'Five', meta: { depth: 3 } },
    ],
  },
};

describe('nodes', () => {
  const initialState = nodes(undefined, {});
  const openState = nodes(initialState, {
    type: 'OPEN_EXPLORER',
    payload: { id: 1 },
  });

  it('exists', () => {
    expect(nodes).toBeDefined();
  });

  it('empty state', () => {
    expect(initialState).toMatchSnapshot();
  });

  it('OPEN_EXPLORER', () => {
    expect(openState).toMatchSnapshot();
  });

  it('GET_PAGE_START', () => {
    const action = { type: 'GET_PAGE_START', payload: { id: 1 } };
    expect(nodes(initialState, action)).toMatchSnapshot();
  });

  it('GET_PAGE_START for an unknown page', () => {
    const action = { type: 'GET_PAGE_START', payload: { id: 2 } };
    const state = nodes(initialState, action);
    expect(state[2].isFetching).toBe(true);
    expect(state[2].isLoaded).toBe(false);
  });

  it('GET_PAGE_SUCCESS', () => {
    const action = {
      type: 'GET_PAGE_SUCCESS',
      payload: { id: 1, data: explorerResponse, offset: 0 },
    };
    expect(nodes(openState, action)).toMatchSnapshot();
  });

  it('GET_PAGE_SUCCESS stores the page details', () => {
    const state = nodes(openState, {
      type: 'GET_PAGE_SUCCESS',
      payload: { id: 1, data: explorerResponse, offset: 0 },
    });

    expect(state[1].isLoaded).toBe(true);
    expect(state[1].isFetching).toBe(false);
    expect(state[1].admin_display_title).toBe('Home');
    expect(state[1].meta.parent.id).toBe(99);
    expect(state[1].translations).toEqual(
      new Map([
        ['fr', 7],
        ['de', 8],
      ]),
    );
    expect(state[1].children).toEqual({ items: [3, 4, 5], count: 5 });
  });

  it('GET_PAGE_SUCCESS stores children as unloaded nodes', () => {
    const state = nodes(openState, {
      type: 'GET_PAGE_SUCCESS',
      payload: { id: 1, data: explorerResponse, offset: 0 },
    });

    expect(state[3].admin_display_title).toBe('Three');
    expect(state[3].isLoaded).toBe(false);
    expect(state[3].meta.parent).toBeUndefined();
  });

  it('GET_PAGE_SUCCESS appends children when loading more', () => {
    const firstState = nodes(openState, {
      type: 'GET_PAGE_SUCCESS',
      payload: { id: 1, data: explorerResponse, offset: 0 },
    });
    const state = nodes(firstState, {
      type: 'GET_PAGE_SUCCESS',
      payload: {
        id: 1,
        offset: 3,
        data: {
          ...explorerResponse,
          children: {
            count: 5,
            items: [
              { id: 6, meta: { depth: 3 } },
              { id: 7, meta: { depth: 3 } },
            ],
          },
        },
      },
    });

    expect(state[1].children).toEqual({ items: [3, 4, 5, 6, 7], count: 5 });
  });

  it('GET_PAGE_SUCCESS ignores more children that do not follow on', () => {
    const firstState = nodes(openState, {
      type: 'GET_PAGE_SUCCESS',
      payload: { id: 1, data: explorerResponse, offset: 0 },
    });
    const state = nodes(firstState, {
      type: 'GET_PAGE_SUCCESS',
      payload: {
        id: 1,
        offset: 20,
        data: {
          ...explorerResponse,
          children: {
            count: 25,
            items: [{ id: 6, meta: { depth: 3 } }],
          },
        },
      },
    });

    expect(state).toBe(firstState);
  });

  it('GET_PAGE_SUCCESS replaces children when reloading', () => {
    const firstState = nodes(openState, {
      type: 'GET_PAGE_SUCCESS',
      payload: { id: 1, data: explorerResponse, offset: 0 },
    });
    const state = nodes(firstState, {
      type: 'GET_PAGE_SUCCESS',
      payload: { id: 1, data: explorerResponse, offset: 0 },
    });

    expect(state[1].children).toEqual({ items: [3, 4, 5], count: 5 });
  });

  it('GET_PAGE_FAILURE', () => {
    const action = { type: 'GET_PAGE_FAILURE', payload: { id: 1 } };
    expect(nodes(openState, action)).toMatchSnapshot();
  });
});
