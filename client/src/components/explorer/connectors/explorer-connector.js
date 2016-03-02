import * as actions from '../actions';


export const mapStateToProps = (state, ownProps) => ({
  visible: state.explorer.react.isVisible,
  page: state.explorer.react.currentPage,
  depth: state.explorer.react.depth,
  loading: state.explorer.react.isLoading,
  fetching: state.explorer.react.isFetching,
  resolved: state.explorer.react.isResolved,
  path: state.explorer.react.path,
  // page: state.explorer.react.page
  // indexes: state.entities.indexes,
  nodes: state.entities.nodes,
  animation: state.explorer.react.animation,
  filter: state.explorer.react.filter,
  transport: state.transport
});

export const mapDispatchToProps = (dispatch) => {
  return {
    setDefaultPage: (id) => { dispatch(actions.setDefaultPage(id)) },
    getChildren: (id) => { dispatch(actions.fetchChildren(id)) },
    onShow: (id) => { dispatch(actions.resetTree(id)); dispatch(actions.fetchTree(id)) },
    onFilter: (filter) => { dispatch(actions.setFilter(filter)) },
    loadItemWithChildren: (id) => { dispatch(actions.fetchPage(id)) },
    pushPage: (id) => { dispatch(actions.pushPage(id)) },
    onPop: () => { dispatch(actions.popPage()) },
    onClose: () => { dispatch(actions.toggleExplorer()) }
  }
}
