import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import * as actions from './actions';

import ExplorerPanel from './ExplorerPanel';

const Explorer = ({
  isVisible,
  page,
  nodes,
  depth,
  gotoPage,
  onClose,
}) => (isVisible ? (
  <ExplorerPanel
    page={nodes[page]}
    nodes={nodes}
    depth={depth}
    onClose={onClose}
    gotoPage={gotoPage}
  />
) : null);

Explorer.propTypes = {
  isVisible: PropTypes.bool.isRequired,
  page: PropTypes.number.isRequired,
  nodes: PropTypes.object.isRequired,
  depth: PropTypes.number.isRequired,

  gotoPage: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

const mapStateToProps = (state) => ({
  isVisible: state.explorer.isVisible,
  page: state.explorer.page,
  nodes: state.nodes,
  depth: state.explorer.depth,
});

const mapDispatchToProps = (dispatch) => ({
  gotoPage: (id, transition) => dispatch(actions.gotoPage(id, transition)),
  onClose: () => dispatch(actions.closeExplorer()),
});

export default connect(mapStateToProps, mapDispatchToProps)(Explorer);
