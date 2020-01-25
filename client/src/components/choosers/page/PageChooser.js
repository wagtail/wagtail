import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import ModalWindow from '../../modal/ModalWindow';

import * as actions from './actions';
import PageChooserBrowseView from './views/PageChooserBrowseView';
import PageChooserSearchView from './views/PageChooserSearchView';
import PageChooserErrorView from './views/PageChooserErrorView';

import { STRINGS } from '../../../config/wagtailConfig';

const getTotalPages = (totalItems, itemsPerPage) =>
  Math.ceil(totalItems / itemsPerPage);

const propTypes = {
  initialParentPageId: PropTypes.any,
  browse: PropTypes.func.isRequired,
  error: PropTypes.node,
  isFetching: PropTypes.bool,
  hasFetched: PropTypes.bool,
  items: PropTypes.array,
  onModalClose: PropTypes.func,
  onPageChosen: PropTypes.func,
  pageTypes: PropTypes.object,
  restrictPageTypes: PropTypes.array,
  parent: PropTypes.func,
  search: PropTypes.func,
  totalItems: PropTypes.number,
  viewName: PropTypes.string,
  viewOptions: PropTypes.object
};

const defaultProps = {
  initialParentPageId: null
};

function PageChooser({
  browse,
  error,
  initialParentPageId,
  isFetching,
  hasFetched,
  items,
  onModalClose,
  onPageChosen,
  pageTypes,
  parent,
  restrictPageTypes,
  search,
  totalItems,
  viewName,
  viewOptions
}) {
  useEffect(() => {
    browse(initialParentPageId || 'root', 1);
  }, []);

  // Event handlers
  const onSearch = queryString => {
    if (queryString) {
      search(queryString, restrictPageTypes, 1);
    } else {
      // Search box is empty, browse instead
      browse('root', 1);
    }
  };

  const onNavigate = page => {
    browse(page.id, 1);
  };

  const onChangePage = newPageNumber => {
    switch (viewName) {
    case 'browse':
      browse(viewOptions.parentPageID, newPageNumber);
      break;
    case 'search':
      search(viewOptions.queryString, restrictPageTypes, newPageNumber);
      break;
    default:
      break;
    }
  };

  // Views
  let view = null;
  switch (viewName) {
  case 'browse':
    view = (
      <PageChooserBrowseView
        parentPage={parent}
        items={items}
        pageTypes={pageTypes}
        restrictPageTypes={restrictPageTypes}
        pageNumber={viewOptions.pageNumber}
        totalPages={getTotalPages(totalItems, 20)}
        onPageChosen={onPageChosen}
        onNavigate={onNavigate}
        onChangePage={onChangePage}
      />
    );
    break;
  case 'search':
    view = (
      <PageChooserSearchView
        items={items}
        totalItems={totalItems}
        pageTypes={pageTypes}
        restrictPageTypes={restrictPageTypes}
        pageNumber={viewOptions.pageNumber}
        totalPages={getTotalPages(totalItems, 20)}
        onPageChosen={onPageChosen}
        onNavigate={onNavigate}
        onChangePage={onChangePage}
      />
    );
    break;
  default:
    break;
  }

  // Check for error
  if (error) {
    view = <PageChooserErrorView errorMessage={error} />;
  }

  // Keyboard controls
  const keydownEventListener = e => {
    if (e.key === 'ArrowLeft') {
      if (parent && viewName === 'browse') {
        const ancestors = parent.meta.ancestors;

        if (ancestors.length > 0) {
          browse(ancestors[ancestors.length - 1].id, 1);
        }
      }
    }
  };

  return (
    <ModalWindow
      heading={STRINGS.CHOOSE_A_PAGE}
      onSearch={onSearch}
      searchEnabled={!error}
      isLoading={isFetching || !hasFetched}
      onClose={onModalClose}
      onKeyDown={keydownEventListener}
    >
      {view}
    </ModalWindow>
  );
}

PageChooser.propTypes = propTypes;
PageChooser.defaultProps = defaultProps;

const mapStateToProps = state => ({
  viewName: state.viewName,
  viewOptions: state.viewOptions,
  parent: state.parent,
  items: state.items,
  totalItems: state.totalItems,
  pageTypes: state.pageTypes,
  hasFetched: state.hasFetched,
  isFetching: state.isFetching,
  error: state.error
});

const mapDispatchToProps = dispatch => ({
  browse: (parentPageID, pageNumber) =>
    dispatch(actions.browse(parentPageID, pageNumber)),
  search: (queryString, restrictPageTypes, pageNumber) =>
    dispatch(actions.search(queryString, restrictPageTypes, pageNumber))
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(PageChooser);
