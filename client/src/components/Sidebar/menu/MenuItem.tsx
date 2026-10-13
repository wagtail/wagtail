import type { MenuAction, MenuState } from '../modules/MainMenu';

export interface MenuItemRenderContext {
  path: string;
  state: MenuState;
  slim: boolean;
  dispatch(action: MenuAction);
  navigate(url: string): Promise<void>;
}

export interface MenuItemDefinition {
  name: string;
  label: string;
  attrs: { [key: string]: any };
  iconName: string | null;
  classNames?: string;
  render(context: MenuItemRenderContext): React.ReactFragment;
}

export interface MenuItemProps<T> {
  path: string;
  slim: boolean;
  state: MenuState;
  item: T;
  dispatch(action: MenuAction): void;
  navigate(url: string): Promise<void>;
}

/**
 * Checks whether a dot-delimited menu path is the same as, or nested within,
 * another menu path. Unlike a plain `startsWith` check, this only matches on
 * whole path segments, so `.qualtrics-360` is not considered to be within
 * `.qualtrics`.
 */
export function isWithinPath(path: string, ancestorPath: string) {
  return path === ancestorPath || path.startsWith(`${ancestorPath}.`);
}

export function isDismissed(item: MenuItemDefinition, state: MenuState) {
  return (
    // Non-dismissibles are considered as dismissed
    !item.attrs['data-w-dismissible-id-value'] ||
    // Dismissed on the server
    'data-w-dismissible-dismissed-value' in item.attrs ||
    // Dismissed on the client
    state.dismissibles[item.name]
  );
}
