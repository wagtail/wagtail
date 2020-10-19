/* eslint-disable react/prop-types */

import React from 'react';
import { connect } from 'react-redux';

import * as actions from './actions';
import { State as NodeState } from './reducers/nodes';

import ExplorerPanel from './ExplorerPanel';

interface ExplorerProps {
  isVisible: boolean;
  path: number[],
  nodes: NodeState,
  onClose(): void;
  popPage(): void;
  pushPage(id: number): void;
}

const Explorer: React.FunctionComponent<ExplorerProps> = ({
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
