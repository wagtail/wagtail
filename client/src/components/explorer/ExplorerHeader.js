import React, { Component } from 'react';
import CSSTransitionGroup from 'react-addons-css-transition-group';
import { EXPLORER_ANIM_DURATION, EXPLORER_FILTERS } from 'config';

import Icon from 'components/icon/Icon';
import Filter from './Filter';

class ExplorerHeader extends Component {

  constructor(p) {
    super(p)
    this.onFilter = this.onFilter.bind(this);
  }

  _getBackBtn() {
    let { onPop } = this.props;

    return (
      <span className='c-explorer__back' onClick={onPop}>
        <Icon name="arrow-left" />
      </span>
    );
  }

  onFilter(e) {
    this.props.onFilter(e.target.value);
  }

  _getClass() {
    let cls = ['c-explorer__trigger'];

    if (this.props.depth > 1) {
      cls.push('c-explorer__trigger--enabled');
    }
    return cls.join(' ');
  }

  _getTitle() {
    let { page, depth } = this.props;

    if (depth < 2 || !page) {
      return 'EXPLORER';
    }

    return page.title;
  }

  render() {
    let { page, depth, filter, onPop, onFilter, transName } = this.props;

    const transitionProps = {
      component: 'span',
      transitionEnterTimeout: EXPLORER_ANIM_DURATION,
      transitionLeaveTimeout: EXPLORER_ANIM_DURATION,
      transitionName: `explorer-${transName}`,
      className: 'c-explorer__rel',
    }

    return (
      <div className="c-explorer__header">
        <span className={this._getClass()} onClick={onPop}>
          { depth > 1 ? this._getBackBtn() : null }
          <span className='u-overflow c-explorer__overflow'>
          <CSSTransitionGroup {...transitionProps}>
            <span className='c-explorer__parent-name' key={depth}>
              {this._getTitle()}
            </span>
          </CSSTransitionGroup>
          </span>
        </span>
        <span className="c-explorer__filter">
          {EXPLORER_FILTERS.map(props => {
            return <Filter key={props.id} {...props} activeFilter={filter} onFilter={onFilter} />
          })}
        </span>
      </div>
    );
  }
}

export default ExplorerHeader;
