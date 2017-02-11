import React from 'react';
import CSSTransitionGroup from 'react-addons-css-transition-group';
import FocusTrap from 'focus-trap-react'

import { EXPLORER_ANIM_DURATION } from '../../config/config';
import { STRINGS } from '../../config/wagtail';


import ExplorerHeader from './ExplorerHeader';
import ExplorerItem from './ExplorerItem';
import LoadingSpinner from './LoadingSpinner';
import PageCount from './PageCount';

export default class ExplorerPanel extends React.Component {
  constructor(props) {
    super(props);
    this.onItemClick = this.onItemClick.bind(this);

    this.state = {
      // TODO Refactor value to constant.
      animation: 'push',
    };
  }

  componentWillReceiveProps(newProps) {
    const { path } = this.props;

    if (path) {
      const isPush = newProps.path.length > path.length;
      const animation = isPush ? 'push' : 'pop';

      this.setState({
        animation: animation,
      });
    }
  }

  loadChildren() {
    const { page, getChildren } = this.props;

    if (page && !page.children.isFetching) {
      if (page.meta.children.count && !page.children.length && !page.children.isFetching && !page.children.isLoaded) {
        getChildren(page.id);
      }
    }
  }

  componentDidUpdate() {
    this.loadChildren();
  }

  componentDidMount() {
    this.props.init();
    document.body.classList.add('explorer-open');
  }

  componentWillUnmount() {
    document.body.classList.remove('explorer-open');
  }

  getClass() {
    const { type } = this.props;
    const cls = ['c-explorer'];

    if (type) {
      cls.push(`c-explorer--${type}`);
    }

    return cls.join(' ');
  }

  onItemClick(id, e) {
    const node = this.props.nodes[id];

    e.preventDefault();
    e.stopPropagation();

    if (node.isLoaded) {
      this.props.pushPage(id);
    } else {
      this.props.loadItemWithChildren(id);
    }
  }

  renderChildren(page) {
    const { nodes, pageTypes } = this.props;

    if (!page || !page.children.items) {
      return [];
    }

    return page.children.items
      .map(index => nodes[index])
      .map((item) => {
        const typeName = pageTypes[item.meta.type] ? pageTypes[item.meta.type].verbose_name : item.meta.type;
        const props = {
          onItemClick: this.onItemClick,
          parent: page,
          key: item.id,
          title: item.title,
          typeName,
          data: item,
        };

        return (
          <ExplorerItem {...props} />
        );
      });
  }

  getContents() {
    const { page } = this.props;
    let ret;

    if (page) {
      if (page.children.items.length) {
        ret = this.renderChildren(page);
      } else {
        ret = (
          <div className="c-explorer__placeholder">{STRINGS.NO_RESULTS}</div>
        );
      }
    }

    return ret;
  }

  render() {
    const {
      page,
      onPop,
      onClose,
      path,
      resolved
    } = this.props;

    // Don't show anything until the tree is resolved.
    if (!resolved) {
      return <div />;
    }

    const headerProps = {
      depth: path.length,
      page,
      onPop,
      onClose,
    };

    const transitionTargetProps = {
      key: path.length,
      className: 'c-explorer__transition-group'
    };

    const transitionProps = {
      component: 'div',
      transitionEnterTimeout: EXPLORER_ANIM_DURATION,
      transitionLeaveTimeout: EXPLORER_ANIM_DURATION,
      transitionName: `explorer-${this.state.animation}`
    };

    const innerTransitionProps = {
      component: 'div',
      transitionEnterTimeout: EXPLORER_ANIM_DURATION,
      transitionLeaveTimeout: EXPLORER_ANIM_DURATION,
      transitionName: 'explorer-fade'
    };

    return (
      <FocusTrap
        paused={page.isFetching}
        focusTrapOptions={{
          onDeactivate: this.props.onClose,
          clickOutsideDeactivates: true,
        }}
      >
        {/* FocusTrap gets antsy while the page is loading, so we give it something to focus on. */}
        {page.isFetching && <div tabIndex={0} />}
        <div className={this.getClass()} tabIndex={-1}>
          <ExplorerHeader {...headerProps} transName={this.state.animation} />
          <div className="c-explorer__drawer">
            <CSSTransitionGroup {...transitionProps}>
              <div {...transitionTargetProps}>
                <CSSTransitionGroup {...innerTransitionProps}>
                  {page.isFetching ? <LoadingSpinner key={1} /> : (
                    <div key={0}>
                      {this.getContents()}
                      {(page.children.count > page.children.items.length) && (
                        <PageCount id={page.id} count={page.meta.children.count} title={page.title} />
                      )}
                    </div>
                  )}
                </CSSTransitionGroup>

              </div>
            </CSSTransitionGroup>
          </div>
        </div>
      </FocusTrap>
    );
  }
}

ExplorerPanel.propTypes = {
  page: React.PropTypes.object,
  onPop: React.PropTypes.func.isRequired,
  onClose: React.PropTypes.func.isRequired,
  type: React.PropTypes.string.isRequired,
  path: React.PropTypes.array,
  resolved: React.PropTypes.bool.isRequired,
  init: React.PropTypes.func.isRequired,
  getChildren: React.PropTypes.func.isRequired,
  pushPage: React.PropTypes.func.isRequired,
  loadItemWithChildren: React.PropTypes.func.isRequired,
  nodes: React.PropTypes.object.isRequired,
  pageTypes: React.PropTypes.object.isRequired,
};
