import React, { Component, PropTypes } from 'react';
import CSSTransitionGroup from 'react-addons-css-transition-group';

import { createStore, combineReducers, applyMiddleware } from 'redux';
import thunkMiddleware from 'redux-thunk'
import createLogger from 'redux-logger'
import { connect } from 'react-redux'

import { EXPLORER_ANIM_DURATION } from 'config';

// Redux mappings
import { mapStateToProps, mapDispatchToProps } from './connectors/explorer-connector';
import rootReducer from './reducers';

// React components
import ExplorerPanel from './explorer-panel';


class Explorer extends Component {
  constructor(props) {
    super(props);
    this._init = this._init.bind(this);
  }

  componentDidMount() {
    if (this.props.defaultPage) {
      this.props.setDefaultPage(this.props.defaultPage);
    }
  }

  _init(id) {
    if (this.props.page && this.props.page.isLoaded) {
      return;
    }

    this.props.onShow(this.props.page ? this.props.page : this.props.defaultPage);
  }

  _getPage() {
    let { nodes, depth, path } = this.props;
    let id = path[path.length - 1];
    return nodes[id];
  }

  render() {
    let { visible, depth, nodes, path, items, type, filter, fetching, resolved } = this.props;
    let page = this._getPage();

    const explorerProps = {
      path,
      page,
      type,
      fetching,
      filter,
      nodes,
      resolved,
      ref: 'explorer',
      left: this.props.left,
      top: this.props.top,
      onPop: this.props.onPop,
      onItemClick: this.props.onItemClick,
      onClose: this.props.onClose,
      transport: this.props.transport,
      onFilter: this.props.onFilter,
      getChildren: this.props.getChildren,
      loadItemWithChildren: this.props.loadItemWithChildren,
      pushPage: this.props.pushPage,
      init: this._init
    }

    const transProps = {
      component: 'div',
      transitionEnterTimeout: EXPLORER_ANIM_DURATION,
      transitionLeaveTimeout: EXPLORER_ANIM_DURATION,
      transitionName: 'explorer-toggle'
    }

    return (
      <CSSTransitionGroup {...transProps}>
        { visible ? <ExplorerPanel {...explorerProps} /> : null }
      </CSSTransitionGroup>
    );
  }
}

Explorer.propTypes = {
  onPageSelect: PropTypes.func,
  initialPath: PropTypes.string,
  apiPath: PropTypes.string,
  size: PropTypes.number,
  position: PropTypes.object,
  page: PropTypes.number,
  defaultPage: PropTypes.number,
};


// =============================================================================
// Connector
// =============================================================================

const VisibleExplorer = connect(
  mapStateToProps,
  mapDispatchToProps
)(Explorer);

const loggerMiddleware = createLogger();

export default VisibleExplorer;
export const store = createStore(
  rootReducer,
  applyMiddleware(loggerMiddleware, thunkMiddleware)
);
