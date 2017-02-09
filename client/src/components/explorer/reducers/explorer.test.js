import * as actions from '../actions';
import _ from 'lodash';
import rootReducer from './index';
import explorer from './explorer';

describe('explorer', () => {
  const initialState = {
    isVisible: false,
    isFetching: false,
    isResolved: false,
    path: [],
    currentPage: 1,
    defaultPage: 1,
    fields: ['title', 'latest_revision_created_at', 'status', 'descendants', 'children'],
    pageTypes: {},
  };

  it('exists', () => {
    expect(explorer).toBeDefined();
  });
  it('returns the initial state if no input is provided', () =>  {
    expect(explorer(undefined, undefined))
      .toEqual(initialState);
  });
  it('sets the default page', () => {
    expect(explorer(initialState, {type: 'SET_DEFAULT_PAGE', payload: 100}))
      .toEqual(_.assign({}, initialState, {defaultPage: 100}))
  });
  it('resets the tree', () => {
    expect(explorer(initialState, {type: 'RESET_TREE', payload: 100}))
      .toEqual(_.assign({}, initialState, {isFetching: true, currentPage: 100}))
  });
  it('has resolved the tree', () => {
    expect(explorer(initialState, {type: 'TREE_RESOLVED'}))
      .toEqual(_.assign({}, initialState, {isResolved: true}))
  });
  it('toggles the explorer', () => {
    expect(explorer(initialState, {type: 'TOGGLE_EXPLORER', payload: 100}))
      .toEqual(
        _.assign({}, initialState, {isVisible: !initialState.isVisible, currentPage: 100})
      )
  });
  it('starts fetching', () => {
    expect(explorer(initialState, {type: 'FETCH_START'}))
      .toEqual(_.assign({}, initialState, {isFetching: true}))
  });
  it('pushes a page to the path', () => {
    expect(explorer(initialState, {type: 'PUSH_PAGE', payload: 100}))
      .toEqual(_.assign({}, initialState, {path: initialState.path.concat([100])}))
  });
  it('pops a page off the path', () => {
    expect(explorer(_.assign({}, initialState, {path: initialState.path.concat(["root", 100])}), {type: 'POP_PAGE', payload: 100}))
      .toEqual(_.assign({}, initialState, {path: initialState.path.concat(["root"])}))
  });
});