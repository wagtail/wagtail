import React from 'react';

import { gettext } from '../../utils/gettext';
import { ADMIN_URLS, LOCALE_NAMES } from '../../config/wagtailConfig';
import Icon from '../Icon/Icon';
import Button from '../Button/Button';
import PublicationStatus from '../PublicationStatus/PublicationStatus';
import { PageState } from './reducers/nodes';

// Hoist icons in the explorer item, as it is re-rendered many times.
const childrenIcon = <Icon name="folder-inverse" className="icon--menuitem" />;

interface PageExplorerItemProps {
  item: PageState;
  onClick(): void;
  navigate(url: string): Promise<void>;
}

/**
 * One menu item in the page explorer, with different available actions
 * and information depending on the metadata of the page.
 */
const PageExplorerItem: React.FunctionComponent<PageExplorerItemProps> = ({
  item,
  onClick,
  navigate,
}) => {
  const { id, admin_display_title: title, meta } = item;
  const hasChildren = meta.children.count > 0;
  const isPublished = meta.status.live && !meta.status.has_unpublished_changes;
  const localeName =
    meta.parent?.id === 1 &&
    meta.locale &&
    (LOCALE_NAMES.get(meta.locale) || meta.locale);

  return (
    <div className="c-page-explorer__item">
      <Button
        href={`${ADMIN_URLS.PAGES}${id}/`}
        navigate={navigate}
        className="c-page-explorer__item__link"
      >
        {hasChildren ? childrenIcon : null}
        <h3 className="c-page-explorer__item__title">{title}</h3>

        {(!isPublished || localeName) && (
          <span className="c-page-explorer__meta">
            {localeName && (
              <span className="o-pill c-status">{localeName}</span>
            )}
            {!isPublished && <PublicationStatus status={meta.status} />}
          </span>
        )}
      </Button>
      <Button
        href={`${ADMIN_URLS.PAGES}${id}/edit/`}
        className="c-page-explorer__item__action c-page-explorer__item__action--small"
        navigate={navigate}
      >
        <Icon
          name="edit"
          title={gettext("Edit '{title}'").replace('{title}', title || '')}
          className="icon--item-action"
        />
      </Button>
      {hasChildren ? (
        <Button
          className="c-page-explorer__item__action"
          onClick={onClick}
          href={`${ADMIN_URLS.PAGES}${id}/`}
          navigate={navigate}
        >
          <Icon
            name="arrow-right"
            title={gettext("View child pages of '{title}'").replace(
              '{title}',
              title || '',
            )}
            className="icon--item-action"
          />
        </Button>
      ) : null}
    </div>
  );
};

export default PageExplorerItem;
