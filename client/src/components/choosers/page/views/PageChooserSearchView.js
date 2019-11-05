import React from 'react';
import PropTypes from 'prop-types';

import { STRINGS } from '../../../../config/wagtailConfig';

import PageChooserResultSet from '../PageChooserResultSet';

// TODO Get rid of any propTypes.
// TODO Figure out whether those values are required or not.
const propTypes = {
  totalItems: PropTypes.number.isRequired,
  pageNumber: PropTypes.any,
  totalPages: PropTypes.any,
  items: PropTypes.any,
  pageTypes: PropTypes.any,
  restrictPageTypes: PropTypes.any,
  onPageChosen: PropTypes.any,
  onNavigate: PropTypes.any,
  onChangePage: PropTypes.any,
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

class PageChooserSearchView extends React.Component {
  render() {
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
    } = this.props;
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
}

PageChooserSearchView.propTypes = propTypes;
// PageChooserSearchView.defaultProps = defaultProps;

export default PageChooserSearchView;
