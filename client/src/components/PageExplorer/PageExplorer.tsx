import React from 'react';
import { connect } from 'react-redux';

import * as actions from './actions';
import { State as NodeState } from './reducers/nodes';
import { State } from './reducers';

import PageExplorerPanel from './PageExplorerPanel';

interface PageExplorerProps {
  isVisible: boolean;
  depth: number;
  currentPageId: number | null;
  nodes: NodeState;
  onClose(): void;
  gotoPage(id: number, transition: number): void;
  navigate(url: string): Promise<void>;
}

const PageExplorer: React.FunctionComponent<PageExplorerProps> = ({
  isVisible,
  depth,
  currentPageId,
  nodes,
  gotoPage,
  onClose,
  navigate,
}) =>
  isVisible && currentPageId ? (
    <PageExplorerPanel
      depth={depth}
      page={nodes[currentPageId]}
      nodes={nodes}
      gotoPage={gotoPage}
      onClose={onClose}
      navigate={navigate}
    />
  ) : null;

const mapStateToProps = (state: State) => ({
  depth: state.explorer.depth,
  currentPageId: state.explorer.currentPageId,
  nodes: state.nodes,
});

const mapDispatchToProps = (dispatch) => ({
  gotoPage: (id: number, transition: number) =>
    dispatch(actions.gotoPage(id, transition)),
});

export default connect(mapStateToProps, mapDispatchToProps)(PageExplorer);
