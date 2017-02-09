import React from 'react';
import CSSTransitionGroup from 'react-addons-css-transition-group';
import { EXPLORER_ANIM_DURATION } from '../../config/config';
import { STRINGS } from '../../config/wagtail';

import Icon from '../../components/Icon/Icon';

const ExplorerHeader = ({ page, depth, onPop, transName }) => {
  const title = depth < 2 || !page ? STRINGS.PAGES : page.title;

  const transitionProps = {
    component: 'span',
    transitionEnterTimeout: EXPLORER_ANIM_DURATION,
    transitionLeaveTimeout: EXPLORER_ANIM_DURATION,
    transitionName: `explorer-${transName}`,
    className: 'c-explorer__rel',
  };

  // TODO Do not use a span for a clickable element.
  return (
    <div className="c-explorer__header">
      <span className={`c-explorer__trigger${depth > 1 ? ' c-explorer__trigger--enabled' : ''}`} onClick={onPop}>
        <span className="u-overflow c-explorer__overflow">
          <CSSTransitionGroup {...transitionProps}>
            <span className="c-explorer__parent-name" key={depth}>
              {depth > 1 ? (
                <span className="c-explorer__back">
                  <Icon name="arrow-left" />
                </span>
              ) : null}
              {title}
            </span>
          </CSSTransitionGroup>
        </span>
      </span>
    </div>
  );
};

ExplorerHeader.propTypes = {
  page: React.PropTypes.object,
  depth: React.PropTypes.number,
  onPop: React.PropTypes.func,
  transName: React.PropTypes.string,
};

export default ExplorerHeader;
