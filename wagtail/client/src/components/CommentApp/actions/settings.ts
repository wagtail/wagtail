import type { SettingsStateUpdate } from '../state/settings';

export const UPDATE_GLOBAL_SETTINGS = 'update-global-settings';

export interface UpdateGlobalSettingsAction {
  type: typeof UPDATE_GLOBAL_SETTINGS;
  update: SettingsStateUpdate;
}

export type Action = UpdateGlobalSettingsAction;

export function updateGlobalSettings(
  update: SettingsStateUpdate,
): UpdateGlobalSettingsAction {
  return {
    type: UPDATE_GLOBAL_SETTINGS,
    update,
  };
}
