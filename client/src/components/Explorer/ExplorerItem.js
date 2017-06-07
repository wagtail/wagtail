import PropTypes from 'prop-types';
import React from 'react';

import { ADMIN_URLS, STRINGS } from '../../config/wagtailConfig';
import Icon from '../../components/Icon/Icon';
import Button from '../../components/Button/Button';
import PublicationStatus from '../../components/PublicationStatus/PublicationStatus';

const ExplorerItem = ({ item, onClick }) => {
  const { id, title, meta } = item;
  const hasChildren = meta.children.count > 0;
  const isPublished = meta.status.live && !meta.status.has_unpublished_changes;

  return (
    <div className="c-explorer__item">
      <Button href={`${ADMIN_URLS.PAGES}${id}/`} className="c-explorer__item__link">
        {hasChildren ? (
          <Icon name="folder-inverse" />
        ) : null}

        <h3 className="c-explorer__item__title">
          {title}
        </h3>

        {!isPublished ? (
          <span className="c-explorer__meta">
            <PublicationStatus status={meta.status} />
          </span>
        ) : null}
      </Button>
      <Button
        href={`${ADMIN_URLS.PAGES}${id}/edit/`}
        className="c-explorer__item__action c-explorer__item__action--small"
      >
        <Icon name="edit" title={`${STRINGS.EDIT} '${title}'`} />
      </Button>
      {hasChildren ? (
        <Button
          className="c-explorer__item__action"
          onClick={onClick}
        >
          <Icon name="arrow-right" title={STRINGS.SEE_CHILDREN} />
        </Button>
      ) : null}
    </div>
  );
};

ExplorerItem.propTypes = {
  item: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    title: PropTypes.string.isRequired,
    meta: PropTypes.shape({
      status: PropTypes.object.isRequired,
    }).isRequired,
  }).isRequired,
  onClick: PropTypes.func.isRequired,
};

export default ExplorerItem;
