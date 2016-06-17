import * as actions from '../actions';
import rootReducer from './index';
import explorer from './explorer';
import nodes from './nodes';
import transport from './transport';

describe('explorer reducers', () => {
  describe('root', () => {
    it('exists', () => {
      expect(rootReducer).toBeDefined();
    });
  });

  describe('explorer', () => {
    it('exists', () => {
      expect(explorer).toBeDefined();
    });
  });

  describe('nodes', () => {
    it('exists', () => {
      expect(nodes).toBeDefined();
    });
  });

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
});
