import React, { Component, PropTypes } from 'react';
import CSSTransitionGroup from 'react-addons-css-transition-group';
import { connect } from 'react-redux'

import * as actions from './actions';
import { EXPLORER_ANIM_DURATION } from 'config';
import ExplorerPanel from './ExplorerPanel';


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
    let { visible, depth, nodes, path, pageTypes, items, type, filter, fetching, resolved } = this.props;
    let page = this._getPage();

    const explorerProps = {
      path,
      pageTypes,
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

const mapStateToProps = (state, ownProps) => ({
  visible: state.explorer.isVisible,
  page: state.explorer.currentPage,
  depth: state.explorer.depth,
  loading: state.explorer.isLoading,
  fetching: state.explorer.isFetching,
  resolved: state.explorer.isResolved,
  path: state.explorer.path,
  pageTypes: state.explorer.pageTypes,
  // page: state.explorer.page
  // indexes: state.entities.indexes,
  nodes: state.nodes,
  animation: state.explorer.animation,
  filter: state.explorer.filter,
  transport: state.transport
});

const mapDispatchToProps = (dispatch) => {
  return {
    setDefaultPage: (id) => { dispatch(actions.setDefaultPage(id)) },
    getChildren: (id) => { dispatch(actions.fetchChildren(id)) },
    onShow: (id) => { dispatch(actions.fetchRoot()) },
    onFilter: (filter) => { dispatch(actions.setFilter(filter)) },
    loadItemWithChildren: (id) => { dispatch(actions.fetchPage(id)) },
    pushPage: (id) => { dispatch(actions.pushPage(id)) },
    onPop: () => { dispatch(actions.popPage()) },
    onClose: () => { dispatch(actions.toggleExplorer()) }
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Explorer);
