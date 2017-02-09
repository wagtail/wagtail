import * as actions from '../actions';
import _ from 'lodash';
import rootReducer from './index';
import transport from './transport';

describe('transport', () => {
  const initialState = {
    error: null,
    showMessage: false,
  };

  it('exists', () => {
    expect(transport).toBeDefined();
  });

  it('returns the initial state', () => {
    expect(transport(undefined, {})).toEqual(initialState);
  });

  it('returns error message and flag', () => {
    const action = actions.fetchFailure(new Error('Test error'));
    expect(transport(initialState, action)).toEqual({
      error: 'Test error',
      showMessage: true,
    });
  });

  it('clears previous error message and flag', () => {
    const action = actions.clearError();
    const errorState = {
      error: 'Test error',
      showMessage: true,
    };
    expect(transport(errorState, action)).toEqual(initialState);
  });
});