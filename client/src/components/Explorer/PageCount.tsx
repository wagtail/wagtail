/* eslint-disable react/prop-types */

import React from 'react';

import { ADMIN_URLS, STRINGS } from '../../config/wagtailConfig';
import Icon from '../Icon/Icon';

interface PageCountProps {
  page: {
    id: number;
    children: {
      count: number;
    }
  }
}

const PageCount: React.FunctionComponent<PageCountProps> = ({ page }) => {
  const count = page.children.count;

  return (
    <a
      href={`${ADMIN_URLS.PAGES}${page.id}/`}
      className="c-explorer__see-more"
    >
      {STRINGS.SEE_ALL}
      <span>{` ${count} ${count === 1 ? STRINGS.PAGE.toLowerCase() : STRINGS.PAGES.toLowerCase()}`}</span>
      <Icon name="arrow-right" />
    </a>
  );
};

export default PageCount;
