import React from 'react';
import { ADMIN_URLS } from '../../config/wagtailConfig';

import { gettext } from '../../utils/gettext';
import Button from '../Button/Button';
import Icon from '../Icon/Icon';
import { PageState } from './reducers/nodes';

interface SelectLocaleProps {
  locale?: string;
  translations: Map<string, number>;
  gotoPage(id: number, transition: number): void;
}

const SelectLocale: React.FunctionComponent<SelectLocaleProps> = ({
  locale,
  translations,
  gotoPage,
}) => {
  /* eslint-disable camelcase */
  const options = wagtailConfig.LOCALES.filter(
    ({ code }) => code === locale || translations.get(code),
  ).map(({ code, display_name }) => (
    <option key={code} value={code}>
      {display_name}
    </option>
  ));
  /* eslint-enable camelcase */

  const onChange = (e) => {
    e.preventDefault();
    const translation = translations.get(e.target.value);
    if (translation) {
      gotoPage(translation, 0);
    }
  };

  return (
    <div className="c-page-explorer__header__select">
      <select value={locale} onChange={onChange} disabled={options.length < 2}>
        {options}
      </select>
      <Icon
        name="arrow-down"
        className="c-page-explorer__header__select-icon"
      />
    </div>
  );
};

interface PageExplorerHeaderProps {
  page: PageState;
  depth: number;
  onClick(e: any): void;
  gotoPage(id: number, transition: number): void;
  navigate(url: string): Promise<void>;
}

/**
 * The bar at the top of the explorer, displaying the current level
 * and allowing access back to the parent level.
 */
const PageExplorerHeader: React.FunctionComponent<PageExplorerHeaderProps> = ({
  page,
  depth,
  onClick,
  gotoPage,
  navigate,
}) => {
  const isRoot = depth === 0;
  const isSiteRoot = page.id === 0;

  return (
    <div className="c-page-explorer__header">
      <Button
        href={!isSiteRoot ? `${ADMIN_URLS.PAGES}${page.id}/` : ADMIN_URLS.PAGES}
        className="c-page-explorer__header__title"
        onClick={onClick}
        navigate={navigate}
      >
        <div className="c-page-explorer__header__title__inner">
          <Icon
            name={isRoot ? 'home' : 'arrow-left'}
            className="icon--explorer-header"
          />
          <span>{page.admin_display_title || gettext('Pages')}</span>
        </div>
      </Button>
      {!isSiteRoot &&
        page.meta.locale &&
        page.translations &&
        page.translations.size > 0 && (
          <SelectLocale
            locale={page.meta.locale}
            translations={page.translations}
            gotoPage={gotoPage}
          />
        )}
    </div>
  );
};

export default PageExplorerHeader;
