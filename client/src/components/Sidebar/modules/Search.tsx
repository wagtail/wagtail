/* eslint-disable react/prop-types */

import React from 'react';

import { ModuleDefinition } from '../Sidebar';

interface SearchInputProps {
    collapsed: boolean;
    searchUrl: string;
    navigate(url: string): void;
}

export const SearchInput: React.FunctionComponent<SearchInputProps> = ({ collapsed, searchUrl, navigate }) => {
  const [isVisible, setIsVisible] = React.useState(false);

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

  React.useEffect(() => {
    if (!collapsed) {
      setIsVisible(true);
    } else if (collapsed && isVisible) {
      // When the menu is collapsed, we have to wait for the close animation
      // to finish before making it invisible
      setTimeout(() => {
        setIsVisible(false);
      }, 300);
    }
  }, [collapsed]);

  return (
    <form className={'sidebar-search' + (collapsed ? ' sidebar-search--collapsed' : '') + (isVisible ? ' sidebar-search--visible' : '')} action={searchUrl} method="get" onSubmit={onSubmitForm}>
      <div>
        <label htmlFor="menu-search-q">{'Search'}</label>{/* GETTEXT */}
        <input type="text" id="menu-search-q" name="q" placeholder={'Search'} />{/* GETTEXT */}
        <button className="button" type="submit">{'Search'}</button>{/* GETTEXT */}
      </div>
    </form>
  );
};

export class SearchModuleDefinition implements ModuleDefinition {
    searchUrl: string;

    constructor(searchUrl: string) {
      this.searchUrl = searchUrl;
    }

    render({ collapsed, navigate }) {
      return <SearchInput collapsed={collapsed} searchUrl={this.searchUrl} navigate={navigate} />;
    }
}
