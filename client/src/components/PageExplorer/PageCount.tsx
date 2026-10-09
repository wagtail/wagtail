import React from 'react';

import { WAGTAIL_CONFIG } from '../../config/wagtailConfig';
import { ngettext } from '../../utils/gettext';
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
      href={`${WAGTAIL_CONFIG.ADMIN_URLS.PAGES}${page.id}/`}
      className="c-page-explorer__see-more"
    >
      {ngettext('See all %(num)s page', 'See all %(num)s pages', count).replace(
        '%(num)s',
        `${count}`,
      )}
      <Icon name="arrow-right" />
    </a>
  );
};

export default PageCount;
