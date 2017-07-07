import PropTypes from 'prop-types';
import React from 'react';
import { ADMIN_URLS, STRINGS } from '../../config/wagtailConfig';

import Button from '../../components/Button/Button';
import Icon from '../../components/Icon/Icon';

/**
 * The bar at the top of the explorer, displaying the current level
 * and allowing access back to the parent level.
 */
const ExplorerHeader = ({ page, depth, onClick }) => {
  const isRoot = depth === 1;

  return (
    <Button
      href={page.id ? `${ADMIN_URLS.PAGES}${page.id}/` : ADMIN_URLS.PAGES}
      className="c-explorer__header"
      onClick={onClick}
    >
      <div className="c-explorer__header__inner">
        <Icon name={isRoot ? 'home' : 'arrow-left'} />
        <span>{page.admin_display_title || STRINGS.PAGES}</span>
      </div>
    </Button>
  );
};

ExplorerHeader.propTypes = {
  page: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    admin_display_title: PropTypes.string,
  }).isRequired,
  depth: PropTypes.number.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default ExplorerHeader;
