import { combineReducers } from 'redux';
import explorer from './explorer';
import nodes from './nodes';
import transport from './transport';


const rootReducer = combineReducers({
  explorer,
  transport,
  nodes,
});

export default rootReducer;
