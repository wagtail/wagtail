/* eslint-disable react/prop-types */

import styled, { css } from 'styled-components';

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

export interface MenuItemWrapperProps {
    isActive: boolean;
    isInSubmenu: boolean;
}

export const MenuItemWrapper = styled.li<MenuItemWrapperProps>`
    a {
        position: relative;
        white-space: nowrap;
        border-left: 3px solid transparent;

        &:before {
            font-size: 1rem;
            vertical-align: -15%;
            margin-right: 0.5em;
        }

        // only really used for spinners and settings menu
        &:after {
            font-size: 1.5em;
            margin: 0;
            position: absolute;
            right: 0.5em;
            top: 0.5em;
            margin-top: 0;
        }

        ${(props) => props.isInSubmenu && css`
            white-space: normal;
            padding: 0.9em 1.7em 0.9em 4.5em;

            &:hover {
                background-color: rgba(100, 100, 100, 0.2);
            }
        `}
    }

    ${(props) => props.isActive && css`
        background: #1a1a1a;  // $nav-item-active-bg;
        text-shadow: -1px -1px 0 rgba(0, 0, 0, 0.3);

        > a {
            border-left-color: #f37e77;  // $color-salmon;
            color: #fff;  // $color-white
        }
    `}
`;

export interface MenuItemProps<T> {
    path: string;
    state: MenuState;
    item: T;
    collapsed: boolean;
    dispatch(action: MenuAction): void;
    navigate(url: string): Promise<void>;
}

