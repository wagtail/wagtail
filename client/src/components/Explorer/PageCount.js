import React from 'react';

import { ADMIN_URLS, STRINGS } from 'config/wagtail';

const PageCount = ({ id, count, title }) => (
  <a
    href={`${ADMIN_URLS.PAGES}${id}/`}
    className="c-explorer__see-more"
  >
    {STRINGS.EXPLORE_ALL_IN}{' '}
    <span className="c-explorer__see-more__title">{title}</span>{' '}
    ({count} {count !== 1 ? STRINGS.PAGES : STRINGS.PAGE})
  </a>
);

PageCount.propTypes = {
  id: React.PropTypes.number.isRequired,
  count: React.PropTypes.number.isRequired,
  title: React.PropTypes.string.isRequired,
};

export default PageCount;
