import React from 'react';

import { gettext } from '../../utils/gettext';
import { ADMIN_URLS } from '../../config/wagtailConfig';
import Icon from '../Icon/Icon';

interface PageCountProps {
  page: {
    id: number;
    children: {
      count: number;
    };
  };
}

const PageCount: React.FunctionComponent<PageCountProps> = ({ page }) => {
  const count = page.children.count;

  return (
    <a
      href={`${ADMIN_URLS.PAGES}${page.id}/`}
      className="c-page-explorer__see-more"
    >
      {gettext('See all')}
      <span>{` ${count} ${
        count === 1
          ? gettext('Page').toLowerCase()
          : gettext('Pages').toLowerCase()
      }`}</span>
      <Icon name="arrow-right" />
    </a>
  );
};

export default PageCount;
