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

  it('GOTO_PAGE', () => {
    expect(explorer(initialState, { type: 'PUSH_PAGE', payload: { id: 100 } })).toMatchSnapshot();
  });
});
