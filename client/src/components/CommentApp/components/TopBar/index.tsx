import React from 'react';

import type { Store } from '../../state';
import { updateGlobalSettings } from '../../actions/settings';

import Checkbox from '../widgets/Checkbox';
import type { TranslatableStrings } from '../../main';

export interface TopBarProps {
  commentsEnabled: boolean;
  store: Store;
  strings: TranslatableStrings;
}

export default function TopBarComponent({
  commentsEnabled,
  store,
  strings,
}: TopBarProps) {
  const onChangeCommentsEnabled = (checked: boolean) => {
    store.dispatch(
      updateGlobalSettings({
        commentsEnabled: checked,
      })
    );
  };

  return (
    <div className="comments-topbar">
      <ul className="comments-topbar__settings">
        <li>
          <Checkbox
            id="show-comments"
            label={strings.SHOW_COMMENTS}
            onChange={onChangeCommentsEnabled}
            checked={commentsEnabled}
          />
        </li>
      </ul>
    </div>
  );
}
