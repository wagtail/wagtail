import React from 'react';
import FocusTrap from 'focus-trap-react';

import { gettext } from '../../utils/gettext';
import { MAX_EXPLORER_PAGES } from '../../config/wagtailConfig';

import LoadingSpinner from '../LoadingSpinner/LoadingSpinner';
import Transition, { PUSH, POP } from '../Transition/Transition';
import PageExplorerHeader from './PageExplorerHeader';
import PageExplorerItem from './PageExplorerItem';
import PageCount from './PageCount';
import { State as NodeState, PageState } from './reducers/nodes';

interface PageExplorerPanelProps {
  nodes: NodeState;
  depth: number;
  page: PageState;
  onClose(): void;
  gotoPage(id: number, transition: number): void;
  navigate(url: string): Promise<void>;
}

interface PageExplorerPanelState {
  transition: typeof PUSH | typeof POP;
}

/**
 * The main panel of the page explorer menu, with heading,
 * menu items, and special states.
 */
class PageExplorerPanel extends React.Component<
  PageExplorerPanelProps,
  PageExplorerPanelState
> {
  constructor(props) {
    super(props);

    this.state = {
      transition: PUSH,
    };

    this.onItemClick = this.onItemClick.bind(this);
    this.onHeaderClick = this.onHeaderClick.bind(this);
  }

  componentWillReceiveProps(newProps) {
    const { depth } = this.props;
    const isPush = newProps.depth > depth;

    this.setState({
      transition: isPush ? PUSH : POP,
    });
  }

  onItemClick(id, e) {
    const { gotoPage } = this.props;

    e.preventDefault();
    e.stopPropagation();

    gotoPage(id, 1);
  }

  onHeaderClick(e) {
    const { page, depth, gotoPage } = this.props;
    const parent = page.meta.parent?.id;

    // Note: Checking depth as well in case the user started deep in the tree
    if (depth > 0 && parent) {
      e.preventDefault();
      e.stopPropagation();

      gotoPage(parent, -1);
    }
  }

  renderChildren() {
    const { page, nodes } = this.props;
    let children;

    if (!page.isFetchingChildren && !page.children.items) {
      children = (
        <div key="empty" className="c-page-explorer__placeholder">
          {gettext('No results')}
        </div>
      );
    } else {
      children = (
        <div key="children">
          {page.children.items.map((id) => (
            <PageExplorerItem
              key={id}
              item={nodes[id]}
              onClick={this.onItemClick.bind(null, id)}
              navigate={this.props.navigate}
            />
          ))}
        </div>
      );
    }

    return (
      <div className="c-page-explorer__drawer">
        {children}
        {page.isFetchingChildren || page.isFetchingTranslations ? (
          <div key="fetching" className="c-page-explorer__placeholder">
            <LoadingSpinner />
          </div>
        ) : null}
        {page.isError ? (
          <div key="error" className="c-page-explorer__placeholder">
            {gettext('Server Error')}
          </div>
        ) : null}
      </div>
    );
  }

  render() {
    const { page, depth, gotoPage, onClose } = this.props;
    const { transition } = this.state;

    return (
      <FocusTrap
        paused={!page || page.isFetchingChildren || page.isFetchingTranslations}
        focusTrapOptions={{
          onDeactivate: onClose,
          clickOutsideDeactivates: false,
          allowOutsideClick: true,
        }}
      >
        <div role="dialog" aria-label={gettext('Page explorer')}>
          <Transition name={transition} className="c-page-explorer">
            <div key={depth} className="c-transition-group">
              <PageExplorerHeader
                depth={depth}
                page={page}
                onClick={this.onHeaderClick}
                gotoPage={gotoPage}
                navigate={this.props.navigate}
              />

              {this.renderChildren()}

              {page.isError ||
              (page.children.items &&
                page.children.count > MAX_EXPLORER_PAGES) ? (
                <PageCount page={page} />
              ) : null}
            </div>
          </Transition>
        </div>
      </FocusTrap>
    );
  }
}

export default PageExplorerPanel;
