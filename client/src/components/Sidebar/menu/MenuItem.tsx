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
