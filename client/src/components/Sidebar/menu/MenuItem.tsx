import { MenuAction, MenuState } from '../modules/MainMenu';

export interface MenuItemRenderContext {
    path: string;
    state: MenuState;
    collapsed: boolean;
    dispatch(action: MenuAction);
    navigate(url: string): Promise<void>;
}

export interface MenuItemDefinition {
    name: string;
    label: string;
    iconName: string | null;
    classNames?: string;
    render(context: MenuItemRenderContext): React.ReactFragment;
}

export interface MenuItemProps<T> {
    path: string;
    state: MenuState;
    item: T;
    collapsed: boolean;
    dispatch(action: MenuAction): void;
    navigate(url: string): Promise<void>;
}

