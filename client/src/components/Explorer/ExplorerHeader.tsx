/* eslint-disable react/prop-types */

import React from 'react';
import { ADMIN_URLS, STRINGS, LOCALE_NAMES } from '../../config/wagtailConfig';

import Button from '../../components/Button/Button';
import Icon from '../../components/Icon/Icon';
import { PageState } from './reducers/nodes';

interface ExplorerHeaderProps {
  page: PageState;
  depth: number;
  onClick(eL: any): void
}

/**
 * The bar at the top of the explorer, displaying the current level
 * and allowing access back to the parent level.
 */
const ExplorerHeader: React.FunctionComponent<ExplorerHeaderProps> = ({ page, depth, onClick }) => {
  const isRoot = depth === 0;
  const isSiteRoot = page.id === 0;

  return (
    <div className="c-explorer__header">
      <Button
        href={!isSiteRoot ? `${ADMIN_URLS.PAGES}${page.id}/` : ADMIN_URLS.PAGES}
        className="c-explorer__header__title "
        onClick={onClick}
      >
        <div className="c-explorer__header__title__inner ">
          <Icon
            name={isRoot ? 'home' : 'arrow-left'}
            className="icon--explorer-header"
          />
          <span>{page.admin_display_title || STRINGS.PAGES}</span>
        </div>
      </Button>
      {!isSiteRoot && page.meta.locale &&
        <div className="c-explorer__header__select">
          <span>{(LOCALE_NAMES.get(page.meta.locale) || page.meta.locale)}</span>
        </div>
      }
    </div>
  );
};

export default ExplorerHeader;
