import React from 'react';
import PropTypes from 'prop-types';

import { STRINGS } from '../../../../config/wagtailConfig';

import PageChooserResultSet from '../PageChooserResultSet';

const propTypes = {
  totalItems: PropTypes.number.isRequired,
  pageNumber: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  items: PropTypes.array,
  pageTypes: PropTypes.object,
  restrictPageTypes: PropTypes.array,
  onPageChosen: PropTypes.func.isRequired,
  onNavigate: PropTypes.func.isRequired,
  onChangePage: PropTypes.func.isRequired,
};

const renderTitle = (totalItems) => {
  switch (totalItems) {
  case 0:
    return STRINGS.THERE_ARE_NO_MATCHES;
  case 1:
    return STRINGS.THERE_IS_ONE_MATCH;
  default:
    return STRINGS.THERE_ARE_N_MATCHES.replace('{count}', totalItems);
  }
};

function PageChooserSearchView(props) {
  const {
    totalItems,
    pageNumber,
    totalPages,
    items,
    pageTypes,
    restrictPageTypes,
    onPageChosen,
    onNavigate,
    onChangePage,
  } = props;

  return (
    <div className="nice-padding">
      <h2>{renderTitle(totalItems)}</h2>
      <PageChooserResultSet
        pageNumber={pageNumber}
        totalPages={totalPages}
        items={items}
        pageTypes={pageTypes}
        restrictPageTypes={restrictPageTypes}
        onPageChosen={onPageChosen}
        onNavigate={onNavigate}
        onChangePage={onChangePage}
      />
    </div>
  );
}

PageChooserSearchView.propTypes = propTypes;
// PageChooserSearchView.defaultProps = defaultProps;

export default PageChooserSearchView;
