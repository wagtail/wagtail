import { createAction } from './actions';

describe('createAction', () => {
  it('should accept an action creator and return a function that creates an action', () => {
    const actionCreator = jest.fn(({ param }) => ({
      data: true,
      hasParam: param,
    }));

    expect(
      createAction('SOME_ACTION_NAME', actionCreator)({ param: true }),
    ).toEqual({
      type: 'SOME_ACTION_NAME',
      payload: { data: true, hasParam: true },
    });

    expect(actionCreator).toHaveBeenCalledWith({ param: true });
  });

  it('should accept an action & meta creator and return a function that creates an action', () => {
    const actionCreator = jest.fn(() => ({ data: true }));

    const metaCreator = jest.fn(() => ({ meta: true }));

    expect(
      createAction(
        'SOME_ACTION_NAME',
        actionCreator,
        metaCreator,
      )({ param: true }),
    ).toEqual({
      type: 'SOME_ACTION_NAME',
      meta: { meta: true },
      payload: { data: true },
    });

    expect(actionCreator).toHaveBeenCalledWith({ param: true });
    expect(metaCreator).toHaveBeenCalledWith({ param: true });
  });
});
