import { expect } from 'chai';

import '../stubs';
import * as actions from 'components/explorer/actions';
import rootReducer from 'components/explorer/reducers';
import explorer from 'components/explorer/reducers/explorer';
import nodes from 'components/explorer/reducers/nodes';
import transport from 'components/explorer/reducers/transport';

describe('explorer reducers', () => {
  describe('root', () => {
    it('exists', () => {
      expect(rootReducer).to.be.a('function');
    });
  });

  describe('explorer', () => {
    it('exists', () => {
      expect(explorer).to.be.a('function');;
    });
  });

  describe('nodes', () => {
    it('exists', () => {
      expect(nodes).to.be.a('function');;
    });
  });

  describe('transport', () => {
    const initialState = {
      error: null,
      showMessage: false,
    };

    it('exists', () => {
      expect(transport).to.be.a('function');;
    });

    it('returns the initial state', () => {
      expect(transport(undefined, {})).to.deep.equal(initialState);
    });

    it('returns error message and flag', () => {
      const action = actions.fetchFailure(new Error('Test error'));
      expect(transport(initialState, action)).to.deep.equal({
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
      expect(transport(errorState, action)).to.deep.equal(initialState);
    });
  });
});
