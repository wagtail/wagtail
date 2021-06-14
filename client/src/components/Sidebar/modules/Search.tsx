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
      <div>
        <label htmlFor="menu-search-q">{strings.SEARCH}</label>
        <input type="text" id="menu-search-q" name="q" placeholder={strings.SEARCH} />
        <button className="button" type="submit">{strings.SEARCH}</button>
      </div>
    </form>
  );
};

export class SearchModuleDefinition implements ModuleDefinition {
  searchUrl: string;

  constructor(searchUrl: string) {
    this.searchUrl = searchUrl;
  }

  render({ slim, expandingOrCollapsing, strings, navigate }) {
    return (
      <SearchInput
        searchUrl={this.searchUrl}
        slim={slim}
        expandingOrCollapsing={expandingOrCollapsing}
        strings={strings}
        navigate={navigate}
      />
    );
  }
}
