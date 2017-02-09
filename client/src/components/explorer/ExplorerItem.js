import React from 'react';

import { ADMIN_URLS, STRINGS } from '../../config/wagtail';
import Icon from '../../components/Icon/Icon';
import Button from '../../components/Button/Button';
import PublicationStatus from '../../components/PublicationStatus/PublicationStatus';
import AbsoluteDate from '../../components/AbsoluteDate/AbsoluteDate';

const ExplorerItem = ({ title, typeName, data, onItemClick }) => {
  const { id, meta } = data;
  const status = meta ? meta.status : null;
  const time = meta ? meta.latest_revision_created_at : null;

  // If we only want pages with children, get this info by
  // looking at the descendants count vs children count.
  // // TODO refactor.
  let count = 0;
  if (meta) {
    count = meta.children.count;
  }
  const hasChildren = count > 0;

  return (
    <Button href={`${ADMIN_URLS.PAGES}${id}`} className="c-explorer__item">
      {hasChildren ? (
        <span
          role="button"
          className="c-explorer__children"
          onClick={onItemClick.bind(null, id)}
        >
          <Icon name="arrow-right" title={STRINGS.SEE_CHILDREN} />
        </span>
      ) : null}

      <h3 className="c-explorer__title">{title}</h3>

      <p className="c-explorer__meta">
        <span className="c-explorer__meta__type">{typeName}</span> | <AbsoluteDate time={time} /> | <PublicationStatus status={status} />
      </p>
    </Button>
  );
};

ExplorerItem.propTypes = {
  title: React.PropTypes.string,
  data: React.PropTypes.object,
  typeName: React.PropTypes.string,
  onItemClick: React.PropTypes.func,
};

ExplorerItem.defaultProps = {
  data: {},
  onItemClick: () => {},
};

export default ExplorerItem;
