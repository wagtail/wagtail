/* eslint-disable react/prop-types */

import React from 'react';

import { ADMIN_URLS, STRINGS, LOCALE_NAMES } from '../../config/wagtailConfig';
import Icon from '../../components/Icon/Icon';
import Button from '../../components/Button/Button';
import PublicationStatus from '../../components/PublicationStatus/PublicationStatus';
import { PageState } from './reducers/nodes';

// Hoist icons in the explorer item, as it is re-rendered many times.
const childrenIcon = (
  <Icon name="folder-inverse" className="icon--menuitem" />
);

interface ExplorerItemProps {
  item: PageState;
  onClick(): void;
}

/**
 * One menu item in the page explorer, with different available actions
 * and information depending on the metadata of the page.
 */
const ExplorerItem: React.FunctionComponent<ExplorerItemProps> = ({ item, onClick }) => {
  const { id, admin_display_title: title, meta } = item;
  const hasChildren = meta.children.count > 0;
  const isPublished = meta.status.live && !meta.status.has_unpublished_changes;
  const localeName = meta.parent?.id === 1 && meta.locale && (LOCALE_NAMES.get(meta.locale) || meta.locale);

  return (
    <div className="c-explorer__item">
      <Button href={`${ADMIN_URLS.PAGES}${id}/`} className="c-explorer__item__link">
        {hasChildren ? childrenIcon : null}

        <h3 className="c-explorer__item__title">
          {title}
        </h3>

        {(!isPublished || localeName) &&
          <span className="c-explorer__meta">
            {localeName && <span className="o-pill c-status">{localeName}</span>}
            {!isPublished && <PublicationStatus status={meta.status} />}
          </span>
        }
      </Button>
      <Button
        href={`${ADMIN_URLS.PAGES}${id}/edit/`}
        className="c-explorer__item__action c-explorer__item__action--small"
      >
        <Icon name="edit" title={STRINGS.EDIT_PAGE.replace('{title}', title)} className="icon--item-action" />
      </Button>
      {hasChildren ? (
        <Button
          className="c-explorer__item__action"
          onClick={onClick}
          href={`${ADMIN_URLS.PAGES}${id}/`}
        >
          <Icon
            name="arrow-right"
            title={STRINGS.VIEW_CHILD_PAGES_OF_PAGE.replace('{title}', title)}
            className="icon--item-action"
          />
        </Button>
      ) : null}
    </div>
  );
};

export default ExplorerItem;
