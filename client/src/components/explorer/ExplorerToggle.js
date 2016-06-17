import React from 'react';
import { connect } from 'react-redux';

import * as actions from './actions';

import Button from '../../components/Button/Button';

/**
 * A Button which toggles the explorer, and doubles as a loading indicator.
 */
// TODO isVisible should not be used here, but at the moment there is a click
// binding problem between this and the ExplorerPanel clickOutside.
const ExplorerToggle = ({ isVisible, isFetching, children, onToggle }) => (
  <Button
    icon="folder-open-inverse"
    isLoading={isFetching}
    onClick={isVisible ? null : onToggle}
  >
    {children}
  </Button>
);

ExplorerToggle.propTypes = {
  isVisible: React.PropTypes.bool,
  isFetching: React.PropTypes.bool,
  onToggle: React.PropTypes.func,
  children: React.PropTypes.node,
};

const mapStateToProps = (store) => ({
  isFetching: store.explorer.isFetching,
  isVisible: store.explorer.isVisible,
});

const mapDispatchToProps = (dispatch) => ({
  onToggle() {
    dispatch(actions.toggleExplorer());
  },
});

export default connect(mapStateToProps, mapDispatchToProps)(ExplorerToggle);
