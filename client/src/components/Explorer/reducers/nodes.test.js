import nodes from './nodes';

describe('nodes', () => {
  const initialState = nodes(undefined, {});

  it('exists', () => {
    expect(nodes).toBeDefined();
  });

  it('empty state', () => {
    expect(initialState).toMatchSnapshot();
  });

  it('OPEN_EXPLORER', () => {
    const action = { type: 'OPEN_EXPLORER', payload: { id: 1 } };
    expect(nodes(initialState, action)).toMatchSnapshot();
  });

  it('GET_PAGE_SUCCESS', () => {
    const action = { type: 'GET_PAGE_SUCCESS', payload: { id: 1, data: {} } };
    expect(nodes(initialState, action)).toMatchSnapshot();
  });

  it('GET_PAGE_FAILURE', () => {
    const state = nodes(initialState, { type: 'OPEN_EXPLORER', payload: { id: 1 } });
    const action = { type: 'GET_PAGE_FAILURE', payload: { id: 1 } };
    expect(nodes(state, action)).toMatchSnapshot();
  });

  it('GET_CHILDREN_START', () => {
    const action = { type: 'GET_CHILDREN_START', payload: { id: 1 } };
    expect(nodes(initialState, action)).toMatchSnapshot();
  });

  it('GET_CHILDREN_SUCCESS', () => {
    const state = nodes(initialState, { type: 'OPEN_EXPLORER', payload: { id: 1 } });
    const action = {
      type: 'GET_CHILDREN_SUCCESS',
      payload: {
        id: 1,
        items: [
          { id: 3 },
          { id: 4 },
          { id: 5 },
        ],
        meta: {
          total_count: 3,
        },
      },
    };
    expect(nodes(state, action)).toMatchSnapshot();
  });

  it('GET_CHILDREN_FAILURE', () => {
    const state = nodes(initialState, { type: 'OPEN_EXPLORER', payload: { id: 1 } });
    const action = { type: 'GET_CHILDREN_FAILURE', payload: { id: 1 } };
    expect(nodes(state, action)).toMatchSnapshot();
  });
});
