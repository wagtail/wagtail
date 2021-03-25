/* eslint-disable react/prop-types */

import React from 'react';
import { connect } from 'react-redux';

import * as actions from './actions';
import { State as NodeState } from './reducers/nodes';
import { State } from './reducers';

import ExplorerPanel from './ExplorerPanel';

interface ExplorerProps {
  isVisible: boolean;
  depth: number,
  currentPageId: number | null,
  nodes: NodeState,
  onClose(): void;
  gotoPage(id: number, transition: number): void;
}

const Explorer: React.FunctionComponent<ExplorerProps> = ({
  isVisible,
  depth,
  currentPageId,
  nodes,
  gotoPage,
  onClose,
}) => ((isVisible && currentPageId) ? (
  <ExplorerPanel
    depth={depth}
    page={nodes[currentPageId]}
    nodes={nodes}
    gotoPage={gotoPage}
    onClose={onClose}
  />
) : null);

const mapStateToProps = (state: State) => ({
  isVisible: state.explorer.isVisible,
  depth: state.explorer.depth,
  currentPageId: state.explorer.currentPageId,
  nodes: state.nodes,
});

const mapDispatchToProps = (dispatch) => ({
  gotoPage: (id: number, transition: number) => dispatch(actions.gotoPage(id, transition)),
  onClose: () => dispatch(actions.closeExplorer()),
});

export default connect(mapStateToProps, mapDispatchToProps)(Explorer);
