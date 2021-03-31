import * as actions from '../actions/settings';
import type { Author } from './comments';
import { update } from './utils';
import produce from "immer";

export interface SettingsState {
  user: Author | null;
  commentsEnabled: boolean;
  showResolvedComments: boolean;
}

export type SettingsStateUpdate = Partial<SettingsState>;

// Reducer with initial state
export const INITIAL_STATE: SettingsState = {
  user: null,
  commentsEnabled: true,
  showResolvedComments: false,
}

export const reducer = produce((draft: SettingsState, action: actions.Action) => {
    switch (action.type) {
        case actions.UPDATE_GLOBAL_SETTINGS:
            update(draft, action.update)
            break
    }
}, INITIAL_STATE)
