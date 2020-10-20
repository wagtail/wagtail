import { State as ExplorerState, Action as ExplorerAction } from './explorer';
import { State as NodeState, Action as NodeAction } from './nodes';

export interface State {
    explorer: ExplorerState,
    nodes: NodeState,
}

export type Action = ExplorerAction | NodeAction;
