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
      // eslint-disable-next-line no-unused-expressions
      expect(rootReducer).to.exist;
    });
  });

  describe('explorer', () => {
    it('exists', () => {
      // eslint-disable-next-line no-unused-expressions
      expect(explorer).to.exist;
    });
  });

  describe('nodes', () => {
    it('exists', () => {
      // eslint-disable-next-line no-unused-expressions
      expect(nodes).to.exist;
    });
  });

  describe('transport', () => {
    const initialState = {
      error: null,
      showMessage: false,
    };

    it('exists', () => {
      // eslint-disable-next-line no-unused-expressions
      expect(transport).to.exist;
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
