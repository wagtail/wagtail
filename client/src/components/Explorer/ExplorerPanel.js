import PropTypes from 'prop-types';
import React from 'react';
import FocusTrap from 'focus-trap-react';

import { STRINGS, MAX_EXPLORER_PAGES } from '../../config/wagtailConfig';

import Button from '../Button/Button';
import LoadingSpinner from '../LoadingSpinner/LoadingSpinner';
import Transition, { PUSH, POP } from '../Transition/Transition';
import ExplorerHeader from './ExplorerHeader';
import ExplorerItem from './ExplorerItem';
import PageCount from './PageCount';

/**
 * The main panel of the page explorer menu, with heading,
 * menu items, and special states.
 */
class ExplorerPanel extends React.Component {
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
    const { path } = this.props;
    const isPush = newProps.path.length > path.length;

    this.setState({
      transition: isPush ? PUSH : POP,
    });
  }

  componentDidMount() {
    document.querySelector('[data-explorer-menu-item]').classList.add('submenu-active');
    document.body.classList.add('explorer-open');
    document.addEventListener('mousedown', this.clickOutside);
    document.addEventListener('touchend', this.clickOutside);
  }

  componentWillUnmount() {
    document.querySelector('[data-explorer-menu-item]').classList.remove('submenu-active');
    document.body.classList.remove('explorer-open');
    document.removeEventListener('mousedown', this.clickOutside);
    document.removeEventListener('touchend', this.clickOutside);
  }

  clickOutside(e) {
    const { onClose } = this.props;
    const explorer = document.querySelector('[data-explorer-menu]');
    const toggle = document.querySelector('[data-explorer-menu-item]');

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
    const { pushPage } = this.props;

    e.preventDefault();
    e.stopPropagation();

    pushPage(id);
  }

  onHeaderClick(e) {
    const { path, popPage } = this.props;
    const hasBack = path.length > 1;

    if (hasBack) {
      e.preventDefault();
      e.stopPropagation();

      popPage();
    }
  }

  renderChildren() {
    const { page, nodes } = this.props;
    let children;

    if (!page.isFetching && !page.children.items) {
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
        {page.isFetching ? (
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
    const { page, onClose, path } = this.props;
    const { transition, paused } = this.state;

    return (
      <FocusTrap
        tag="nav"
        className="explorer"
        paused={paused || !page || page.isFetching}
        focusTrapOptions={{
          initialFocus: '.c-explorer__close',
          onDeactivate: onClose,
        }}
      >
        <Button className="c-explorer__close u-hidden" onClick={onClose}>
          {STRINGS.CLOSE_EXPLORER}
        </Button>
        <Transition name={transition} className="c-explorer">
          <div key={path.length} className="c-transition-group">
            <ExplorerHeader
              depth={path.length}
              page={page}
              onClick={this.onHeaderClick}
            />

            {this.renderChildren()}

            {page.isError || page.children.items && page.children.count > MAX_EXPLORER_PAGES ? (
              <PageCount page={page} />
            ) : null}
          </div>
        </Transition>
      </FocusTrap>
    );
  }
}

ExplorerPanel.propTypes = {
  nodes: PropTypes.object.isRequired,
  path: PropTypes.array.isRequired,
  page: PropTypes.shape({
    isFetching: PropTypes.bool,
    children: PropTypes.shape({
      count: PropTypes.number,
      items: PropTypes.array,
    }),
  }).isRequired,
  onClose: PropTypes.func.isRequired,
  popPage: PropTypes.func.isRequired,
  pushPage: PropTypes.func.isRequired,
};

export default ExplorerPanel;
