/* eslint-disable react/prop-types */

import * as React from 'react';

import { ModuleDefinition, Strings } from '../Sidebar';

interface SearchInputProps {
  slim: boolean;
  expandingOrCollapsing: boolean;
  searchUrl: string;
  strings: Strings;
  navigate(url: string): void;
}

export const SearchInput: React.FunctionComponent<SearchInputProps> = (
  { slim, expandingOrCollapsing, searchUrl, strings, navigate }) => {
  const isVisible = !slim || expandingOrCollapsing;

  const onSubmitForm = (e: React.FormEvent<HTMLFormElement>) => {
    if (e.target instanceof HTMLFormElement) {
      e.preventDefault();

      if (isVisible) {
        const inputElement = e.target.querySelector('input[name="q"]') as HTMLInputElement;
        navigate(searchUrl + '?q=' + encodeURIComponent(inputElement.value));
      } else {
        navigate(searchUrl);
      }
    }
  };

  const className = (
    'sidebar-search'
    + (slim ? ' sidebar-search--slim' : '')
    + (isVisible ? ' sidebar-search--visible' : '')
  );

  return (
    <form className={className} action={searchUrl} method="get" onSubmit={onSubmitForm}>
      <label className="sidebar-search__label" htmlFor="menu-search-q">{strings.SEARCH}</label>
      <input className="sidebar-search__input" type="text" id="menu-search-q" name="q" placeholder={strings.SEARCH} />
      <button className="button sidebar-search__submit" type="submit">{strings.SEARCH}</button>
    </form>
  );
};

export class SearchModuleDefinition implements ModuleDefinition {
  searchUrl: string;

  constructor(searchUrl: string) {
    this.searchUrl = searchUrl;
  }

  render({ slim, key, expandingOrCollapsing, strings, navigate }) {
    return (
      <SearchInput
        searchUrl={this.searchUrl}
        slim={slim}
        key={key}
        expandingOrCollapsing={expandingOrCollapsing}
        strings={strings}
        navigate={navigate}
      />
    );
  }
}
