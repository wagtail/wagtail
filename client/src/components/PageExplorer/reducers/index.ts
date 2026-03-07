import {
  Action as PageExplorerAction,
  State as PageExplorerState,
} from './explorer';
import { Action as NodeAction, State as NodeState } from './nodes';

export interface State {
  explorer: PageExplorerState;
  nodes: NodeState;
}

export type Action = PageExplorerAction | NodeAction;
