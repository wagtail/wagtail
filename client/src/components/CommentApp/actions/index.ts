import type { Action as CommentsAction } from './comments';
import type { Action as SettingsActon } from './settings';

export type Action = CommentsAction | SettingsActon;
