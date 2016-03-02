import { combineReducers } from 'redux';
import react from './explorer-reducer';
import nodes from './node-reducer';
import transport from './transport-reducer.js';


const rootReducer = combineReducers({
  explorer: combineReducers({
    react
  }),
  transport,
  entities: combineReducers({
    nodes
  }),
});

export default rootReducer;
