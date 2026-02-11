import * as React from 'react';
import type { MenuAction, MenuState } from '../modules/MainMenu';
import type { MenuItemDefinition } from './MenuItem';

export function renderMenu(
  path: string,
  items: MenuItemDefinition[],
  slim: boolean,
  state: MenuState,
  dispatch: (action: MenuAction) => void,
  navigate: (url: string) => Promise<void>,
) {
  return (
    <>
      {items.map((item) =>
        item.render({
          path: `${path}.${item.name}`,
          slim,
          state,
          dispatch,
          navigate,
        }),
      )}
    </>
  );
}
