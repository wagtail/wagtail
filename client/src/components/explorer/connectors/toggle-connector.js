export function mapStateToProps(store) {
  return {
    loading: store.explorer.react.isFetching,
    visible: store.explorer.react.isVisible,
  }
}

export function mapDispatchToProps(dispatch) {
  return {
    onToggle: (id) => {
      dispatch({ type: 'TOGGLE_EXPLORER', id })
    }
  }
};
