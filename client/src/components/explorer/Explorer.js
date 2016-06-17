import React from 'react';
import CSSTransitionGroup from 'react-addons-css-transition-group';
import { connect } from 'react-redux';

import * as actions from './actions';
import { EXPLORER_ANIM_DURATION } from '../../config/config';
import ExplorerPanel from './ExplorerPanel';

// TODO To refactor.
class Explorer extends React.Component {
  constructor(props) {
    super(props);
    this.init = this.init.bind(this);
  }

  componentDidMount() {
    if (this.props.defaultPage) {
      this.props.setDefaultPage(this.props.defaultPage);
    }
  }

  init() {
    if (this.props.page && this.props.page.isLoaded) {
      return;
    }

    this.props.onShow(this.props.page ? this.props.page : this.props.defaultPage);
  }

  getPage() {
    const { nodes, path } = this.props;
    const id = path[path.length - 1];
    return nodes[id];
  }

  render() {
    const { isVisible, nodes, path, pageTypes, type, filter, fetching, resolved } = this.props;
    const page = this.getPage();

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
      onPop: this.props.onPop,
      onClose: this.props.onClose,
      transport: this.props.transport,
      onFilter: this.props.onFilter,
      getChildren: this.props.getChildren,
      loadItemWithChildren: this.props.loadItemWithChildren,
      pushPage: this.props.pushPage,
      init: this.init,
    };

    const transProps = {
      component: 'div',
      transitionEnterTimeout: EXPLORER_ANIM_DURATION,
      transitionLeaveTimeout: EXPLORER_ANIM_DURATION,
      transitionName: 'explorer-toggle'
    };

    return (
      <CSSTransitionGroup {...transProps}>
        {isVisible ? <ExplorerPanel {...explorerProps} /> : null}
      </CSSTransitionGroup>
    );
  }
}

Explorer.propTypes = {
  isVisible: React.PropTypes.bool.isRequired,
  fetching: React.PropTypes.bool.isRequired,
  resolved: React.PropTypes.bool.isRequired,
  path: React.PropTypes.array,
  type: React.PropTypes.string.isRequired,
  filter: React.PropTypes.string.isRequired,
  nodes: React.PropTypes.object.isRequired,
  transport: React.PropTypes.object.isRequired,
  page: React.PropTypes.any,
  defaultPage: React.PropTypes.number,
  onPop: React.PropTypes.func.isRequired,
  setDefaultPage: React.PropTypes.func.isRequired,
  onShow: React.PropTypes.func.isRequired,
  onClose: React.PropTypes.func.isRequired,
  onFilter: React.PropTypes.func.isRequired,
  getChildren: React.PropTypes.func.isRequired,
  loadItemWithChildren: React.PropTypes.func.isRequired,
  pushPage: React.PropTypes.func.isRequired,
  pageTypes: React.PropTypes.object.isRequired,
};

const mapStateToProps = (state) => ({
  isVisible: state.explorer.isVisible,
  page: state.explorer.currentPage,
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

const mapDispatchToProps = (dispatch) => ({
  setDefaultPage: (id) => dispatch(actions.setDefaultPage(id)),
  getChildren: (id) => dispatch(actions.fetchChildren(id)),
  onShow: () => dispatch(actions.fetchRoot()),
  onFilter: (filter) => dispatch(actions.setFilter(filter)),
  loadItemWithChildren: (id) => dispatch(actions.fetchPage(id)),
  pushPage: (id) => dispatch(actions.pushPage(id)),
  onPop: () => dispatch(actions.popPage()),
  onClose: () => dispatch(actions.toggleExplorer()),
});

export default connect(mapStateToProps, mapDispatchToProps)(Explorer);
