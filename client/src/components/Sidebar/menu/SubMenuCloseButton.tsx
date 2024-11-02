import * as React from 'react';
import { createPortal } from 'react-dom';

import Icon from '../../Icon/Icon';
import { gettext } from '../../../utils/gettext';
import { MenuAction } from '../modules/MainMenu';

interface SubMenuCloseButtonProps {
  isVisible: boolean;
  dispatch(action: MenuAction): void;
}

export default function SubMenuCloseButton({
  isVisible,
  dispatch,
}: SubMenuCloseButtonProps) {
  if (!isVisible) {
    return null;
  }
  return createPortal(
    <button
      type="button"
      onClick={() =>
        dispatch({
          type: 'set-navigation-path',
          path: '',
        })
      }
      className="button sidebar-close-menu-button"
      aria-label={gettext('Close')}
    >
      <Icon name="cross" className="w-w-[15px] w-h-4" />
    </button>,
    document.body,
  );
}
