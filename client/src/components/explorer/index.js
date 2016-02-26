import React, { Component, PropTypes } from 'react';
import LoadingIndicator from 'components/loading-indicator';
import ExplorerItem from './explorer-item';

import thunkMiddleware from 'redux-thunk'
import createLogger from 'redux-logger'

import { API } from 'config';
import { createStore, combineReducers, applyMiddleware } from 'redux';
import { connect } from 'react-redux'


const loggerMiddleware = createLogger();


function react(state = {
    isVisible: false,
    isFetching: false,
    depth: -1,
    nodes: [],
    title: null,
  }, action) {

  switch (action.type) {
    case 'TOGGLE_EXPLORER':
      return Object.assign({}, state, {
        isVisible: !state.isVisible
      });
    case 'FETCH_START':
      return Object.assign({}, state, {
        isFetching: true
      });
    case 'FETCH_COMPLETE':
      let nodes = state.nodes;

      if (state.nodes.indexOf(action.id) < 0) {
        nodes = state.nodes.concat([action.id]);
      }

      return Object.assign({}, state, {
        isFetching: false,
        nodes,
        depth: state.depth + 1,
        title: action.title,
      });
    case 'PUSH_PAGE':
      return Object.assign({}, state, {
        depth: state.depth + 1
      });
    case 'POP_PAGE':
      return Object.assign({}, state, {
        depth: state.depth > 0 ? state.depth - 1 : 0
      });
  }
  return state;
}


const explorer = combineReducers({
  react
});


// Pages reducer

function pages(state = [], action) {
  switch (action.type) {
    case 'FETCH_START':
      return Object.assign({}, state, {
        [action.id]: {
          isFetching: true,
          isError: false,
          meta: {},
          items: []
        }
      });
    case 'FETCH_COMPLETE':
      return Object.assign({}, state, {
        [action.id]: {
          isFetching: false,
          isError: false,
          meta: action.body.meta,
          items: action.body.items
        }
      });
    case 'FETCH_ERROR':
      return Object.assign({}, state, {
        [action.id]: {
          isFetching: false,
          isError: true,
          message: action.body.message ? action.body.message: ''
        }
      });
  }

  return state;
}

const entities = combineReducers({
  pages
});

const rootReducer = combineReducers({
  explorer,
  entities
});



// filter...
// const getVisibleItems = (items, filter) => {
//   switch (filter) {
//     case 'SHOW_ALL':
//       return items
//     case 'SHOW_DRAFT':
//       return items.filter(t => t.meta.state === 'draft')
//     case 'SHOW_LIVE':
//       return items.filter(t => !t.meta.state === 'live')
//   }
// }




// =============================================================================
// Actions
// =============================================================================

function fetchStart(id, title) {
  return {
    type: 'FETCH_START',
    id,
    title
  };
}

function fetchComplete(id, body, title) {
  return {
    type: 'FETCH_COMPLETE',
    id,
    body,
    title,
  };
}

function fetchError(id, body) {
  return {
    type: 'FETCH_ERROR',
    id,
    body
  }
}

const pushPage = (id) => {
  return {
    type: 'PUSH_PAGE',
    id: id
  }
}

const popPage = (id) => {
  return {
    type: 'POP_PAGE',
    id: id
  }
}

function _json() {
  let reqHeaders = new Headers();
  reqHeaders.append('Content-Type', 'application/json');

  return {
    method: 'GET',
    headers: reqHeaders,
    credentials: 'same-origin'
  };
}


function fetchPage(id='root', title='') {
  return dispatch => {
    dispatch(fetchStart(id))
    return fetch(`${API}/pages/?child_of=${id}`, _json())
      .then(response => response.json())
      .then(json => dispatch(fetchComplete(id, json, title)))
      .catch(json => dispatch(fetchError(id, json, title)))
  }
}


const PageCount = ({ id, count }) => {
  if (count === 0) {
    return null;
  }

  return (
    <div onClick={() => { window.location.href = `/admin/pages/${id}/` }} className="c-explorer__see-more">
      See { count } { count === 1 ? 'child' : 'children'}
    </div>
  );
}


// =============================================================================
// Klass
// =============================================================================


class ExplorerHeader extends Component {
  backBtn() {
    let { onPop } = this.props;
    return <span className='c-explorer__back' onClick={onPop}><span className="icon icon-arrow-left"></span> </span>
  }

  closeBtn() {
    let { onClose } = this.props;
    return <span className='c-explorer__back' onClick={onClose}>{'×'}</span>
  }

  render() {
    let { page, depth, title } = this.props;

    return (
      <div className="c-explorer__header">
        { depth > 0 ? this.backBtn() : null }
        { depth > 0 ? title : 'EXPLORER' }
      </div>
    );
  }
}

const ExplorerEmpty = () => {
  return <div className='c-explorer__placeholder'>No pages</div>
}

class Explorer extends Component {

  componentDidMount() {
    this.props.onShow();
  }

  componentWillUnmount() {

  }

  _getChildren(node) {
    if (!node) {
      return [];
    }

    return node.items.map(item =>
      <ExplorerItem
        onItemClick={this.props.onItemClick}
        key={item.id}
        title={item.title}
        data={item} />
    );
  }

  _getStyle() {
    const { top, left, fill } = this.props;
    return {
      left: left + 'px',
      top: top + 'px',
      height: fill ? '100vh' : null
    };
  }

  _getPage() {
    let { nodes, depth, pages } = this.props;
    let id = nodes[depth];
    return pages[id];
  }

  render() {
    let { visible, loading, depth, nodes, pages, title } = this.props;
    let id = nodes[depth];
    let page = this._getPage();
    let children = this._getChildren(page);

    if (!visible) {
      return null;
    }

    return (
      <div style={this._getStyle()} className="c-explorer">
        <ExplorerHeader title={title} depth={depth} page={page} onPop={this.props.onPop} onClose={this.props.onClose}/>
        <div className='c-explorer__drawer'>
        { loading ? <LoadingIndicator /> : (children.length ? children : <ExplorerEmpty />) }
        </div>
        <PageCount id={id} count={page.meta.total_count} />
      </div>
    );
  }
}

Explorer.propTypes = {
  onPageSelect: PropTypes.func,
  initialPath: PropTypes.string,
  apiPath: PropTypes.string,
  size: PropTypes.number,
  position: PropTypes.object
};


// =============================================================================
// Connector
// =============================================================================

const mapStateToProps = (state, ownProps) => ({
  visible: state.explorer.react.isVisible,
  page: state.explorer.currentPage,
  react: state.explorer.react,
  depth: state.explorer.react.depth,
  title: state.explorer.react.title,
  loading: state.explorer.react.isLoading,
  nodes: state.explorer.react.nodes,
  pages: state.entities.pages,
});

const mapDispatchToProps = (dispatch) => {
  return {
    onShow: (id) => { dispatch(fetchPage(id)) },
    onItemClick: (id, title) => { dispatch(fetchPage(id, title)) },
    onPop: () => { dispatch(popPage()) },
    onClose: () => { dispatch({ type: 'TOGGLE_EXPLORER' }) }
  }
}

const VisibleExplorer = connect(
  mapStateToProps,
  mapDispatchToProps
)(Explorer);

export default VisibleExplorer;

export const store = createStore(
  rootReducer,
  applyMiddleware(loggerMiddleware, thunkMiddleware)
);
