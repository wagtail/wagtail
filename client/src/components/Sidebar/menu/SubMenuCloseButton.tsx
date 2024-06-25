import * as React from 'react';
import { createPortal } from 'react-dom';

import Icon from '../../Icon/Icon';
import { gettext } from '../../../utils/gettext';

export default function SubMenuCloseButton({isVisible, dispatch}) {
  if (!isVisible) {
    return null;
  }
  return createPortal(
    <button
      type="button"
      onClick={
        () => dispatch({
          type: 'set-navigation-path',
          path: '',
        })
      }
      className="button sidebar-close-menu-button"
      aria-label={gettext('Close submenu')}
    >
      <Icon name="cross" className="w-w-[15px] w-h-4" />
    </button>,
    document.body
  )
}


