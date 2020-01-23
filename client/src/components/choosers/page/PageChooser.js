import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import ModalWindow from '../../modal/ModalWindow';

import * as actions from './actions';
import PageChooserHeader from './PageChooserHeader';
import PageChooserSpinner from './PageChooserSpinner';
import PageChooserBrowseView from './views/PageChooserBrowseView';
import PageChooserSearchView from './views/PageChooserSearchView';
import PageChooserErrorView from './views/PageChooserErrorView';

const getTotalPages = (totalItems, itemsPerPage) => Math.ceil(totalItems / itemsPerPage);

const propTypes = {
  initialParentPageId: PropTypes.any,
  browse: PropTypes.func.isRequired,
};

const defaultProps = {
  initialParentPageId: null,
};

class PageChooser extends ModalWindow {
  componentDidMount() {
    const { browse, initialParentPageId, onModalClose } = this.props;

    browse(initialParentPageId || 'root', 1);

    // Focus the search box
    document.getElementById(`${this.state.id}-search`).focus();

    document.addEventListener('keydown', onModalClose);
  }

  componentWillUnmount() {
    const { onModalClose } = this.props;

    document.removeEventListener('keydown', onModalClose);
  }

  renderModalContents() {
    const {
      browse,
      error,
      isFetching,
      items,
      onPageChosen,
      pageTypes,
      parent,
      restrictPageTypes,
      search,
      totalItems,
      viewName,
      viewOptions,
    } = this.props;
    // Event handlers
    const onSearch = (queryString) => {
      if (queryString) {
        search(queryString, restrictPageTypes, 1);
      } else {
        // Search box is empty, browse instead
        browse('root', 1);
      }
    };

    const onNavigate = (page) => {
      browse(page.id, 1);
    };

    const onChangePage = (newPageNumber) => {
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

    return (
      <div>
        <PageChooserHeader modalId={this.state.id} onSearch={onSearch} searchEnabled={!error} />
        <PageChooserSpinner isActive={isFetching}>
          {view}
        </PageChooserSpinner>
      </div>
    );
  }
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
  isFetching: state.isFetching,
  error: state.error,
});

const mapDispatchToProps = dispatch => ({
  browse: (parentPageID, pageNumber) => dispatch(actions.browse(parentPageID, pageNumber)),
  search: (queryString, restrictPageTypes, pageNumber) =>
    dispatch(actions.search(queryString, restrictPageTypes, pageNumber)),
});

export default connect(mapStateToProps, mapDispatchToProps)(PageChooser);
