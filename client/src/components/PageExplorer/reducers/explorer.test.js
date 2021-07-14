import explorer from './explorer';

describe('explorer', () => {
  const initialState = explorer(undefined, {});

  it('exists', () => {
    expect(explorer).toBeDefined();
  });

  it('returns the initial state if no input is provided', () =>  {
    expect(explorer(undefined, {})).toEqual(initialState);
  });

  it('OPEN_EXPLORER', () => {
    const action = { type: 'OPEN_EXPLORER', payload: { id: 1 } };
    expect(explorer(initialState, action)).toMatchSnapshot();
  });

  it('CLOSE_EXPLORER', () => {
    expect(explorer(initialState, { type: 'CLOSE_EXPLORER' })).toEqual(initialState);
  });

  it('PUSH_PAGE', () => {
    expect(explorer(initialState, { type: 'PUSH_PAGE', payload: { id: 100 } })).toMatchSnapshot();
  });

  it('POP_PAGE', () => {
    const state = explorer(initialState, { type: 'PUSH_PAGE', payload: { id: 100 } });
    const action = { type: 'POP_PAGE', payload: { id: 100 } };
    expect(explorer(state, action)).toMatchSnapshot();
  });
});
