/* eslint-disable react/prop-types */

import React from 'react';
import FocusTrap from 'focus-trap-react';

import { STRINGS, MAX_EXPLORER_PAGES } from '../../config/wagtailConfig';

import Button from '../Button/Button';
import LoadingSpinner from '../LoadingSpinner/LoadingSpinner';
import Transition, { PUSH, POP } from '../Transition/Transition';
import ExplorerHeader from './ExplorerHeader';
import ExplorerItem from './ExplorerItem';
import PageCount from './PageCount';
import { State as NodeState, PageState } from './reducers/nodes';

interface ExplorerPanelProps {
  nodes: NodeState;
  depth: number;
  page: PageState;
  onClose(): void;
  gotoPage(id: number, transition: number): void;
}

interface ExplorerPanelState {
  transition: typeof PUSH | typeof POP;
  paused: boolean;
}

/**
 * The main panel of the page explorer menu, with heading,
 * menu items, and special states.
 */
class ExplorerPanel extends React.Component<ExplorerPanelProps, ExplorerPanelState> {
  constructor(props) {
    super(props);

    this.state = {
      transition: PUSH,
      paused: false,
    };

    this.onItemClick = this.onItemClick.bind(this);
    this.onHeaderClick = this.onHeaderClick.bind(this);
    this.clickOutside = this.clickOutside.bind(this);
  }

  componentWillReceiveProps(newProps) {
    const { depth } = this.props;
    const isPush = newProps.depth > depth;

    this.setState({
      transition: isPush ? PUSH : POP,
    });
  }

  componentDidMount() {
    document.querySelector('[data-explorer-menu-item]')?.classList.add('submenu-active');
    document.body.classList.add('explorer-open');
    document.addEventListener('mousedown', this.clickOutside);
    document.addEventListener('touchend', this.clickOutside);
  }

  componentWillUnmount() {
    document.querySelector('[data-explorer-menu-item]')?.classList.remove('submenu-active');
    document.body.classList.remove('explorer-open');
    document.removeEventListener('mousedown', this.clickOutside);
    document.removeEventListener('touchend', this.clickOutside);
  }

  clickOutside(e) {
    const { onClose } = this.props;
    const explorer = document.querySelector('[data-explorer-menu]');
    const toggle = document.querySelector('[data-explorer-menu-item]');

    if (!explorer || !toggle) {
      return;
    }

    const isInside = explorer.contains(e.target) || toggle.contains(e.target);
    if (!isInside) {
      onClose();
    }

    if (toggle.contains(e.target)) {
      this.setState({
        paused: true,
      });
    }
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
        <div key="empty" className="c-explorer__placeholder">
          {STRINGS.NO_RESULTS}
        </div>
      );
    } else {
      children = (
        <div key="children">
          {page.children.items.map((id) => (
            <ExplorerItem
              key={id}
              item={nodes[id]}
              onClick={this.onItemClick.bind(null, id)}
            />
          ))}
        </div>
      );
    }

    return (
      <div className="c-explorer__drawer">
        {children}
        {page.isFetchingChildren || page.isFetchingTranslations ? (
          <div key="fetching" className="c-explorer__placeholder">
            <LoadingSpinner />
          </div>
        ) : null}
        {page.isError ? (
          <div key="error" className="c-explorer__placeholder">
            {STRINGS.SERVER_ERROR}
          </div>
        ) : null}
      </div>
    );
  }

  render() {
    const { page, onClose, depth, gotoPage } = this.props;
    const { transition, paused } = this.state;

    return (
      <FocusTrap
        paused={paused || !page || page.isFetchingChildren || page.isFetchingTranslations}
        focusTrapOptions={{
          initialFocus: '.c-explorer__header__title',
          onDeactivate: onClose,
        }}
      >
        <div
          role="dialog"
          className="explorer"
        >
          <Button className="c-explorer__close">
            {STRINGS.CLOSE_EXPLORER}
          </Button>
          <Transition name={transition} className="c-explorer" component="nav" label={STRINGS.PAGE_EXPLORER}>
            <div key={depth} className="c-transition-group">
              <ExplorerHeader
                depth={depth}
                page={page}
                onClick={this.onHeaderClick}
                gotoPage={gotoPage}
              />

              {this.renderChildren()}

              {page.isError || page.children.items && page.children.count > MAX_EXPLORER_PAGES ? (
                <PageCount page={page} />
              ) : null}
            </div>
          </Transition>
        </div>
      </FocusTrap>
    );
  }
}

export default ExplorerPanel;
