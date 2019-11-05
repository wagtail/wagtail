import React from 'react';
import PropTypes from 'prop-types';

import { STRINGS } from '../../../../config/wagtailConfig';

import PageChooserResultSet from '../PageChooserResultSet';

const propTypes = {
  pageNumber: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  parentPage: PropTypes.object,
  items: PropTypes.array,
  pageTypes: PropTypes.object,
  restrictPageTypes: PropTypes.array,
  onPageChosen: PropTypes.func.isRequired,
  onNavigate: PropTypes.func.isRequired,
  onChangePage: PropTypes.func.isRequired,
};

const defaultProps = {
  parentPage: null,
};

class PageChooserBrowseView extends React.Component {
  renderBreadcrumb() {
    const { parentPage, onNavigate } = this.props;
    let breadcrumbItems = null;

    if (parentPage) {
      const ancestorPages = parentPage.meta.ancestors;

      breadcrumbItems = ancestorPages.map((ancestorPage) => {
        const onClickNavigate = (e) => {
          onNavigate(ancestorPage);
          e.preventDefault();
        };

        if (ancestorPage.id === 1) {
          return (
            <li key={ancestorPage.id} className="home">
              <a
                href="#"
                className="navigate-pages icon icon-home text-replace"
                onClick={onClickNavigate}
              >
                {STRINGS.HOME}
              </a>
            </li>
          );
        }

        return (
          <li key={ancestorPage.id}>
            <a
              href="#"
              className="navigate-pages"
              onClick={onClickNavigate}
            >
              {ancestorPage.title}
            </a>
          </li>
        );
      });
    }

    return (
      <ul className="breadcrumb">
        {breadcrumbItems}
      </ul>
    );
  }
  render() {
    const {
      pageNumber,
      totalPages,
      parentPage,
      items,
      pageTypes,
      restrictPageTypes,
      onPageChosen,
      onNavigate,
      onChangePage,
    } = this.props;

    return (
      <div className="nice-padding">
        <h2>{STRINGS.EXPLORER}</h2>
        {this.renderBreadcrumb()}
        <PageChooserResultSet
          pageNumber={pageNumber}
          totalPages={totalPages}
          parentPage={parentPage}
          items={items}
          pageTypes={pageTypes}
          restrictPageTypes={restrictPageTypes}
          displayChildNavigation={true}
          onPageChosen={onPageChosen}
          onNavigate={onNavigate}
          onChangePage={onChangePage}
        />
      </div>
    );
  }
}

PageChooserBrowseView.propTypes = propTypes;
PageChooserBrowseView.defaultProps = defaultProps;

export default PageChooserBrowseView;
