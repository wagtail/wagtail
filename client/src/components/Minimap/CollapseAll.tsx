import React from 'react';
import { gettext } from '../../utils/gettext';

import Icon from '../Icon/Icon';

export interface CollapseAllProps {
  expanded: boolean;
  floating?: boolean;
  insideMinimap: boolean;
  onClick: () => void;
}

/**
 * "Collapse all" button UI, without any collapsing logic.
 */
const CollapseAll: React.FunctionComponent<CollapseAllProps> = ({
  expanded,
  floating,
  insideMinimap,
  onClick,
}) => (
  <button
    type="button"
    aria-expanded={expanded}
    onClick={onClick}
    className={`button button-small button-secondary w-minimap__collapse-all ${
      floating ? 'w-minimap__collapse-all--floating' : ''
    } ${insideMinimap ? 'w-minimap__collapse-all--inside' : ''}`}
  >
    <Icon name={expanded ? 'collapse-up' : 'collapse-down'} />
    {expanded ? gettext('Collapse all') : gettext('Expand all')}
  </button>
);

export default CollapseAll;
