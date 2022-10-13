import React, { useState } from 'react';
import { gettext } from '../../utils/gettext';

import Icon from '../Icon/Icon';

export interface CollapseAllProps {
  onClick: (expanded: boolean) => void;
}

/**
 * TODO;
 */
const CollapseAll: React.FunctionComponent<CollapseAllProps> = ({
  onClick,
}) => {
  const [expanded, setExpanded] = useState<boolean>(true);

  return (
    <button
      type="button"
      aria-expanded={expanded}
      onClick={() => {
        setExpanded(!expanded);
        onClick(!expanded);
      }}
      className="button button-small button-secondary w-minimap__collapse-all"
    >
      <Icon name={expanded ? 'arrow-up-big' : 'arrow-down-big'} />
      {expanded ? gettext('Collapse all') : gettext('Expand all')}
    </button>
  );
};

export default CollapseAll;
