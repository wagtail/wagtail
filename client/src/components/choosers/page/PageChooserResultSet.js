import React from 'react';
import PropTypes from 'prop-types';

import { STRINGS } from '../../../config/wagtailConfig';

import PageChooserPagination from './PageChooserPagination';
import PageChooserResult from './PageChooserResult';

const propTypes = {
  displayChildNavigation: PropTypes.bool,
  restrictPageTypes: PropTypes.array,
  items: PropTypes.array,
  onPageChosen: PropTypes.func.isRequired,
  onNavigate: PropTypes.func.isRequired,
  pageTypes: PropTypes.object,
  parentPage: PropTypes.any,
  pageNumber: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  onChangePage: PropTypes.func.isRequired,
};

const defaultProps = {
  displayChildNavigation: false,
  restrictPageTypes: [],
  items: [],
  pageTypes: {},
  parentPage: null,
};

class PageChooserResultSet extends React.Component {
  pageIsNavigable(page) {
    const { displayChildNavigation } = this.props;

    return displayChildNavigation && page.meta.children.count > 0;
  }

  pageIsChoosable(page) {
    const { restrictPageTypes } = this.props;
    if (restrictPageTypes != null && restrictPageTypes.indexOf(page.meta.type.toLowerCase()) === -1) {
      return false;
    }

    return true;
  }

  render() {
    const { items,
      onPageChosen,
      onNavigate,
      pageTypes,
      parentPage,
      pageNumber,
      totalPages,
      onChangePage } = this.props;

    const results = items.map((page, i) => {
      const onChoose = (e) => {
        onPageChosen(page);
        e.preventDefault();
      };

      const handleNavigate = (e) => {
        onNavigate(page);
        e.preventDefault();
      };

      return (
        <PageChooserResult
          key={i}
          page={page}
          isChoosable={this.pageIsChoosable(page)}
          isNavigable={this.pageIsNavigable(page)}
          onChoose={onChoose}
          onNavigate={handleNavigate}
          pageTypes={pageTypes}
        />
      );
    });

    // Parent page
    let parent = null;

    if (parentPage) {
      const onChoose = (e) => {
        onPageChosen(parentPage);
        e.preventDefault();
      };

      const handleNavigate = (e) => {
        onNavigate(parentPage);
        e.preventDefault();
      };

      parent = (
        <PageChooserResult
          page={parentPage}
          isParent={true}
          isChoosable={this.pageIsChoosable(parentPage)}
          isNavigable={false}
          onChoose={onChoose}
          onNavigate={handleNavigate}
          pageTypes={pageTypes}
        />
      );
    }

    return (
      <div className="page-results">
        <table className="listing  chooser">
          <colgroup>
            <col />
            <col width="12%" />
            <col width="12%" />
            <col width="12%" />
            <col width="10%" />
          </colgroup>
          <thead>
            <tr className="table-headers">
              <th className="title">{STRINGS.TITLE}</th>
              <th className="updated">{STRINGS.UPDATED}</th>
              <th className="type">{STRINGS.TYPE}</th>
              <th className="status">{STRINGS.STATUS}</th>
              <th />
            </tr>
            {parent}
          </thead>
          <tbody>
            {results}
          </tbody>
        </table>

        <PageChooserPagination
          pageNumber={pageNumber}
          totalPages={totalPages}
          onChangePage={onChangePage}
        />
      </div>
    );
  }
}

PageChooserResultSet.propTypes = propTypes;
PageChooserResultSet.defaultProps = defaultProps;

export default PageChooserResultSet;
