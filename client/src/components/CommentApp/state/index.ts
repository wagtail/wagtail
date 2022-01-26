import { combineReducers, Store as reduxStore } from 'redux';

import { reducer as commentsReducer } from './comments';
import { reducer as settingsReducer } from './settings';
import type { Action } from '../actions';

export type State = ReturnType<typeof reducer>;

export const reducer = combineReducers({
  comments: commentsReducer,
  settings: settingsReducer,
});

export type Store = reduxStore<State, Action>;
