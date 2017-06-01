import PropTypes from 'prop-types';
import React from 'react';

import { ADMIN_URLS, STRINGS } from '../../config/wagtailConfig';
import Icon from '../Icon/Icon';

const PageCount = ({ page }) => {
  const count = page.children.count;

  return (
    <a
      href={`${ADMIN_URLS.PAGES}${page.id}/`}
      className="c-explorer__see-more"
      tabIndex={0}
    >
      {STRINGS.SEE_ALL}
      <span>{` ${count} ${count === 1 ? STRINGS.PAGE.toLowerCase() : STRINGS.PAGES.toLowerCase()}`}</span>
      <Icon name="arrow-right" />
    </a>
  );
};

PageCount.propTypes = {
  page: PropTypes.object.isRequired,
};

export default PageCount;
