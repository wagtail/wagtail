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
    const { init } = this.props;

    init();
    document.body.classList.add('explorer-open');
  }

  componentWillUnmount() {
    document.body.classList.remove('explorer-open');
  }

  onItemClick(id, e) {
    const { nodes, pushPage, loadItemWithChildren } = this.props;
    const node = nodes[id];

    e.preventDefault();
    e.stopPropagation();

    if (node.isLoaded) {
      pushPage(id);
    } else {
      loadItemWithChildren(id);
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

        return (
          <ExplorerItem
            onItemClick={this.onItemClick}
            parent={page}
            key={item.id}
            title={item.title}
            typeName={typeName}
            data={item}
          />
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
          <div className="c-explorer__placeholder">
            {STRINGS.NO_RESULTS}
          </div>
        );
      }
    }

    return ret;
  }

  render() {
    const { type, page, onPop, onClose, path, resolved } = this.props;
    const { animation } = this.state;

    return !resolved ? (
      <div />
    ) : (
      <FocusTrap
        paused={page.isFetching}
        focusTrapOptions={{
          onDeactivate: onClose,
          clickOutsideDeactivates: true,
        }}
      >
        {/* FocusTrap gets antsy while the page is loading, so we give it something to focus on. */}
        {page.isFetching && <div tabIndex={0} />}
        <div className={`c-explorer ${type ? 'c-explorer--' + type : ''}`} tabIndex={-1}>
          <ExplorerHeader
            depth={path.length}
            page={page}
            onPop={onPop}
            onClose={onClose}
            transName={animation}
          />
          <div className="c-explorer__drawer">
            <CSSTransitionGroup
              component="div"
              transitionEnterTimeout={EXPLORER_ANIM_DURATION}
              transitionLeaveTimeout={EXPLORER_ANIM_DURATION}
              transitionName={`explorer-${animation}`}
            >
              <div key={path.length} className="c-explorer__transition-group">
                <CSSTransitionGroup
                  component="div"
                  transitionEnterTimeout={EXPLORER_ANIM_DURATION}
                  transitionLeaveTimeout={EXPLORER_ANIM_DURATION}
                  transitionName="explorer-fade"
                >
                  {page.isFetching ? (
                    <LoadingSpinner key={1} />
                  ) : (
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
