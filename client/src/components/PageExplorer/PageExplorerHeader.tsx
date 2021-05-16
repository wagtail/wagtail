/* eslint-disable react/prop-types */

import React from 'react';
import { ADMIN_URLS, STRINGS } from '../../config/wagtailConfig';

import Button from '../../components/Button/Button';
import Icon from '../../components/Icon/Icon';
import { PageState } from './reducers/nodes';

interface SelectLocaleProps {
  locale?: string;
  translations: Map<string, number>;
  gotoPage(id: number, transition: number): void;
}

const SelectLocale: React.FunctionComponent<SelectLocaleProps> = ({ locale, translations, gotoPage }) => {
  const options = wagtailConfig.LOCALES
    .filter(({ code }) => code === locale || translations.get(code))
    /* eslint-disable-next-line camelcase */
    .map(({ code, display_name }) => <option key={code} value={code}>{display_name}</option>);

  const onChange = (e) => {
    e.preventDefault();
    const translation = translations.get(e.target.value);
    if (translation) {
      gotoPage(translation, 0);
    }
  };

  return (
    <div className="c-page-explorer__header__select">
      <select value={locale} onChange={onChange} disabled={options.length < 2}>{options}</select>
      <span></span>
    </div>
  );
};

interface PageExplorerHeaderProps {
  page: PageState;
  depth: number;
  onClick(e: any): void
  gotoPage(id: number, transition: number): void;
  navigate(url: string): Promise<void>;
}

/**
 * The bar at the top of the explorer, displaying the current level
 * and allowing access back to the parent level.
 */
const PageExplorerHeader: React.FunctionComponent<PageExplorerHeaderProps> = (
  { page, depth, onClick, gotoPage, navigate }) => {
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
          <span>{page.admin_display_title || STRINGS.PAGES}</span>
        </div>
      </Button>
      {!isSiteRoot && page.meta.locale &&
      page.translations &&
      page.translations.size > 0 &&
        <SelectLocale locale={page.meta.locale} translations={page.translations} gotoPage={gotoPage} />}
    </div>
  );
};

export default PageExplorerHeader;
