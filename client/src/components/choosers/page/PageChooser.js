import React from 'react';
import { connect } from 'react-redux';

import { BaseChooser } from '../BaseChooser';

import * as actions from './actions';
import PageChooserHeader from './PageChooserHeader';
import PageChooserBrowseView from './views/PageChooserBrowseView';
import PageChooserSearchView from './views/PageChooserSearchView';


// TODO PageChooserExternalLinkView
// TODO PageChooserEmailView


function getTotalPages(totalItems, itemsPerPage) {
  return Math.ceil(totalItems / itemsPerPage);
}


class PageChooserSpinner extends React.Component {
  render() {
    if (this.props.isActive) {
      return (
        <div className="loading-mask loading">
          {this.props.children}
        </div>
      );
    } else {
      return (
        <div className="loading-mask">
          {this.props.children}
        </div>
      );
    }
  }
}


class PageChooserErrorView extends React.Component {
  render() {
    return (
      <div className="nice-padding">
        <div className="help-block help-critical">
          {this.props.errorMessage}
        </div>
      </div>
    );
  }
}


class PageChooser extends BaseChooser {
  renderModalContents() {
    // Event handlers
    let onSearch = (queryString) => {
      if (queryString) {
        this.props.search(queryString, this.props.restrictPageTypes, 1);
      } else {
        // Search box is empty, browse instead
        this.props.browse('root', 1);
      }
    }

    let onNavigate = (page) => {
      this.props.browse(page.id, 1);
    };

    let onChangePage = (newPageNumber) => {
      switch (this.props.viewName) {
        case 'browse':
          this.props.browse(this.props.viewOptions.parentPageID, newPageNumber);
          break;
        case 'search':
          this.props.search(this.props.viewOptions.queryString, this.props.restrictPageTypes, newPageNumber);
          break;
      }
    };

    // Views
    let view = null;
    switch (this.props.viewName) {
      case 'browse':
        view = <PageChooserBrowseView parentPage={this.props.parent} items={this.props.items} pageTypes={this.props.pageTypes} restrictPageTypes={this.props.restrictPageTypes} pageNumber={this.props.viewOptions.pageNumber} totalPages={getTotalPages(this.props.totalItems, 20)} onPageChosen={this.props.onPageChosen} onNavigate={onNavigate} onChangePage={onChangePage} />;
        break;
      case 'search':
        view = <PageChooserSearchView items={this.props.items} totalItems={this.props.totalItems} pageTypes={this.props.pageTypes} restrictPageTypes={this.props.restrictPageTypes} pageNumber={this.props.viewOptions.pageNumber} totalPages={getTotalPages(this.props.totalItems, 20)} onPageChosen={this.props.onPageChosen} onNavigate={onNavigate} onChangePage={onChangePage} />;
        break;
    }

    // Check for error
    if (this.props.error) {
      view = <PageChooserErrorView errorMessage={this.props.error} />;
    }

    return (
      <div>
        <PageChooserHeader onSearch={onSearch} searchEnabled={!this.props.error} />
        <PageChooserSpinner isActive={this.props.isFetching}>
          {view}
        </PageChooserSpinner>
      </div>
    );
  }

  componentDidMount() {
    this.props.browse(this.props.initialParentPageId || 'root', 1);
  }
}


const mapStateToProps = (state) => ({
  viewName: state.viewName,
  viewOptions: state.viewOptions,
  parent: state.parent,
  items: state.items,
  totalItems: state.totalItems,
  pageTypes: state.pageTypes,
  isFetching: state.isFetching,
  error: state.error,
});

const mapDispatchToProps = (dispatch) => ({
  browse: (parentPageID, pageNumber) => dispatch(actions.browse(parentPageID, pageNumber)),
  search: (queryString, restrictPageTypes, pageNumber) => dispatch(actions.search(queryString, restrictPageTypes, pageNumber)),
});

export default connect(mapStateToProps, mapDispatchToProps)(PageChooser);
