import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import * as actions from './actions';

import ExplorerPanel from './ExplorerPanel';

const Explorer = ({
  isVisible,
  nodes,
  path,
  pushPage,
  popPage,
  onClose,
}) => {
  const page = nodes[path[path.length - 1]];

  return isVisible ? (
    <ExplorerPanel
      path={path}
      page={page}
      nodes={nodes}
      onClose={onClose}
      popPage={popPage}
      pushPage={pushPage}
    />
  ) : null;
};

Explorer.propTypes = {
  isVisible: PropTypes.bool.isRequired,
  path: PropTypes.array.isRequired,
  nodes: PropTypes.object.isRequired,

  pushPage: PropTypes.func.isRequired,
  popPage: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

const mapStateToProps = (state) => ({
  isVisible: state.explorer.isVisible,
  path: state.explorer.path,
  nodes: state.nodes,
});

const mapDispatchToProps = (dispatch) => ({
  pushPage: (id) => dispatch(actions.pushPage(id)),
  popPage: () => dispatch(actions.popPage()),
  onClose: () => dispatch(actions.closeExplorer()),
});

export default connect(mapStateToProps, mapDispatchToProps)(Explorer);
