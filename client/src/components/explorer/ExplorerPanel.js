import React, { Component, PropTypes } from 'react';
import CSSTransitionGroup from 'react-addons-css-transition-group';
import { EXPLORER_ANIM_DURATION } from 'config';

import ExplorerEmpty from './ExplorerEmpty';
import ExplorerHeader from './ExplorerHeader';
import ExplorerItem from './ExplorerItem';
import LoadingSpinner from './LoadingSpinner';

export default class ExplorerPanel extends Component {
  constructor(props) {
    super(props);
    this._clickOutside = this._clickOutside.bind(this);
    this._onItemClick = this._onItemClick.bind(this);
    this.closeModal = this.closeModal.bind(this);

    this.state = {
      modalIsOpen: false,
      animation: 'push',
    }
  }

  componentWillReceiveProps(newProps) {
    let oldProps = this.props;

    if (!oldProps.path) {
      return;
    }

    if (newProps.path.length > oldProps.path.length) {
      return this.setState({ animation: 'push' });
    } else {
      return this.setState({ animation: 'pop' });
    }
  }

  _loadChildren() {
    let { page } = this.props;

    if (!page || page.children.isFetching) {
      return false;
    }

    if (page.meta.children.count && !page.children.length && !page.children.isFetching && !page.children.isLoaded) {
      this.props.getChildren(page.id);
    }
  }

  componentDidUpdate() {
    this._loadChildren();
  }

  componentDidMount() {
    this.props.init();

    document.body.style.overflow = 'hidden';
    document.body.classList.add('u-explorer-open');
    document.addEventListener('click', this._clickOutside);
  }

  componentWillUnmount() {
    document.body.style.overflow = '';
    document.body.classList.remove('u-explorer-open');
    document.removeEventListener('click', this._clickOutside);
  }

  _clickOutside(e) {
    let { explorer } = this.refs;

    if (!explorer) {
      return;
    }

    if (!explorer.contains(e.target)) {
      this.props.onClose();
    }
  }

  _getStyle() {
    const { top, left } = this.props;
    return {
      left: left + 'px',
      top: top + 'px'
    };
  }

  _getClass() {
    let { type } = this.props;
    let cls = ['c-explorer'];

    if (type) {
      cls.push(`c-explorer--${type}`);
    }

    return cls.join(' ');
  }

  closeModal() {
    const { dispatch } = this.props;
    dispatch(clearError());
    this.setState({
      modalIsOpen: false
    });
  }

  _onItemClick(id) {
    let node = this.props.nodes[id];

    if (node.isLoaded) {
      this.props.pushPage(id);
    } else {
      this.props.loadItemWithChildren(id);
    }
  }

  renderChildren(page) {
    let { nodes, pageTypes, filter } = this.props;

    if (!page || !page.children.items) {
      return [];
    }

    return page.children.items.map(index => {
      return nodes[index];
    }).map(item => {
      const typeName = pageTypes[item.meta.type] ? pageTypes[item.meta.type].verbose_name : item.meta.type;
      const props = {
        onItemClick: this._onItemClick,
        parent: page,
        key: item.id,
        title: item.title,
        typeName,
        data: item,
        filter,
      };

      return <ExplorerItem {...props} />
    });
  }

  _getContents() {
    let { page } = this.props;
    let contents = null;

    if (page) {
      if (page.children.items.length) {
        return this.renderChildren(page)
      } else {
        return <ExplorerEmpty />
      }
    }
  }

  render() {
    let {
      page,
      onPop,
      onClose,
      loading,
      type,
      pageData,
      transport,
      onFilter,
      filter,
      path,
      resolved
    } = this.props;

    // Don't show anything until the tree is resolved.
    if (!this.props.resolved) {
      return <div />
    }

    const headerProps = {
      depth: path.length,
      page,
      onPop,
      onClose,
      onFilter,
      filter
    }

    const transitionTargetProps = {
      key: path.length,
      className: 'c-explorer__transition-group'
    }

    const transitionProps = {
      component: 'div',
      transitionEnterTimeout: EXPLORER_ANIM_DURATION,
      transitionLeaveTimeout: EXPLORER_ANIM_DURATION,
      transitionName: `explorer-${this.state.animation}`
    }

    const innerTransitionProps = {
      component: 'div',
      transitionEnterTimeout: EXPLORER_ANIM_DURATION,
      transitionLeaveTimeout: EXPLORER_ANIM_DURATION,
      transitionName: `explorer-fade`
    }

    return (
      <div style={this._getStyle()} className={this._getClass()} ref='explorer'>
        <ExplorerHeader {...headerProps} transName={this.state.animation} />
        <div className='c-explorer__drawer'>
          <CSSTransitionGroup {...transitionProps}>
            <div {...transitionTargetProps}>
              <CSSTransitionGroup {...innerTransitionProps}>
                {page.isFetching ? <LoadingSpinner key={1} /> : (
                  <div key={0}>
                    {this._getContents()}
                  </div>
              )}
              </CSSTransitionGroup>

            </div>
          </CSSTransitionGroup>
        </div>
      </div>
    )
  }
}

ExplorerPanel.propTypes = {

}
