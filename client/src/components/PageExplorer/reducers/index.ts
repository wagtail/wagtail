import {
  State as PageExplorerState,
  Action as PageExplorerAction,
} from './explorer';
import { State as NodeState, Action as NodeAction } from './nodes';

export interface State {
  explorer: PageExplorerState;
  nodes: NodeState;
}

export type Action = PageExplorerAction | NodeAction;
