import * as React from 'react';

import Icon from '../../Icon/Icon';
import { ModuleDefinition, Strings } from '../Sidebar';

interface SearchInputProps {
  slim: boolean;
  expandingOrCollapsing: boolean;
  onSearchClick: () => void;
  onSearchBlur: () => void;
  searchUrl: string;
  strings: Strings;
  navigate(url: string): void;
}

export const SearchInput: React.FunctionComponent<SearchInputProps> = ({
  slim,
  expandingOrCollapsing,
  onSearchClick,
  onSearchBlur,
  searchUrl,
  strings,
  navigate,
}) => {
  const isVisible = !slim || expandingOrCollapsing;

  const onSubmitForm = (e: React.FormEvent<HTMLFormElement>) => {
    if (e.target instanceof HTMLFormElement) {
      e.preventDefault();

      if (isVisible) {
        const inputElement = e.target.querySelector(
          'input[name="q"]',
        ) as HTMLInputElement;
        navigate(searchUrl + '?q=' + encodeURIComponent(inputElement.value));
      } else {
        navigate(searchUrl);
      }
    }
  };

  const className =
    'sidebar-search' +
    (slim ? ' sidebar-search--slim' : '') +
    (isVisible ? ' sidebar-search--visible' : '');

  return (
    <form
      role="search"
      className={className}
      action={searchUrl}
      method="get"
      onSubmit={onSubmitForm}
    >
      <button
        className="button sidebar-search__submit"
        type="submit"
        aria-label={strings.SEARCH}
      >
        <Icon className="icon--menuitem" name="search" />
      </button>
      <label className="sidebar-search__label" htmlFor="menu-search-q">
        {strings.SEARCH}
      </label>
      <input
        className="sidebar-search__input"
        type="text"
        id="menu-search-q"
        name="q"
        placeholder={strings.SEARCH}
        onClick={() => {
          onSearchClick();
        }}
        onBlur={() => onSearchBlur()}
      />
    </form>
  );
};

export class SearchModuleDefinition implements ModuleDefinition {
  searchUrl: string;

  constructor(searchUrl: string) {
    this.searchUrl = searchUrl;
  }

  render({
    slim,
    key,
    expandingOrCollapsing,
    onSearchClick,
    onSearchBlur,
    strings,
    navigate,
  }) {
    return (
      <SearchInput
        searchUrl={this.searchUrl}
        slim={slim}
        key={key}
        expandingOrCollapsing={expandingOrCollapsing}
        onSearchClick={onSearchClick}
        onSearchBlur={onSearchBlur}
        strings={strings}
        navigate={navigate}
      />
    );
  }
}
