import produce from 'immer';
import * as actions from '../actions/settings';
import type { Author } from './comments';
import { update } from './utils';

export interface SettingsState {
  user: Author | null;
  commentsEnabled: boolean;
  currentTab: string | null;
}

export type SettingsStateUpdate = Partial<SettingsState>;

// Reducer with initial state
export const INITIAL_STATE: SettingsState = {
  user: null,
  commentsEnabled: false,
  currentTab: null,
};

export const reducer = produce(
  (draft: SettingsState, action: actions.Action) => {
    switch (action.type) {
      case actions.UPDATE_GLOBAL_SETTINGS:
        update(draft, action.update);
        break;
      default:
        break;
    }
  },
  INITIAL_STATE,
);
