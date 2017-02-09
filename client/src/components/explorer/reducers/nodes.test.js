import * as actions from '../actions';
import _ from 'lodash';
import rootReducer from './index';
import nodes from './nodes';

describe('nodes', () => {
  const initialState = {
    isError: false,
    isFetching: false,
    isLoaded: false,
    children: {
      items: [],
      count: 0,
      isFetching: false
    }
  };

  const fetchingState = {
    "any": {
      isFetching: true,
      isError: false,
      isLoaded: false,
      children: {
        items: [],
        count: 0,
        isFetching: false
      }
    }
  };

  const fetchingChildren = {
    isError: false,
    isFetching: false,
    isLoaded: false,
    children: {
      items: [],
      count: 0,
      isFetching: false
    },
    "any": {
      isFetching: true,
      children: {
        items: [],
        count: 0,
        isFetching: true
      }
    }
  };

  it('exists', () => {
    expect(nodes).toBeDefined();
  });

  it('returns empty state on no action and no input state', () => {
    expect(nodes(undefined, undefined)).toEqual({});
  });
  it('returns initial state on no action and initial state input', () => {
    expect(nodes(initialState, undefined)).toEqual(initialState);
  });
  it('starts fetching children', () => {
    expect(nodes(initialState, {type: 'FETCH_CHILDREN_START', payload: 'any'})).toEqual(fetchingChildren);
  });
  it('resets the tree', () => {
    expect(nodes({}, {type: 'RESET_TREE'})).toEqual(initialState);
  });
  it('starts fetching', () => {
    expect(nodes({}, {type: 'FETCH_START', payload: 'any'})).toEqual(fetchingState)
  });
  it('makes a fetch success', () => {
    expect(nodes({'any': 'any'}, {type: 'FETCH_SUCCESS'})).toEqual({'any': 'any'})
  })
});
