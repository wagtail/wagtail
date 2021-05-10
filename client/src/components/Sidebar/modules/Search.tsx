/* eslint-disable react/prop-types */

import React from 'react';
import styled, { css } from 'styled-components';

import * as mixins from '../common/mixins';
import { getIcon } from '../common/iconfont';
import { ModuleDefinition } from '../Sidebar';

interface SearchFormProps {
    collapsed: boolean;
    visible: boolean;
}

const SearchForm = styled.form<SearchFormProps>`
    position: relative;
    padding: 0 1em 1em;
    margin: 0;
    width: 100%;
    box-sizing: border-box;

    label {
        ${mixins.visuallyhidden()}
    }

    input,
    button {
        border-radius: 0;
        font-size: 1em;
        border: 0;
    }

    input {
        cursor: pointer;
        border: 1px solid #999;  // #999 = $nav-search-border;
        background-color: #333;  // $nav-search-bg;
        color: #ccc;  // $nav-search-color;
        padding: 0.8em 2.5em 0.8em 1em;
        font-weight: 600;
        opacity: 1;
        // Need !important to override body.ready class
        transition: background-color 0.2s ease, opacity 0.3s ease !important;

        ${(props) => props.collapsed && css`
            opacity: 0;
        `}

        ${(props) => !props.visible && css`
            visibility: hidden;
        `}

        &:hover {
            background-color: hsla(0,0%,39.2%,.15);  // $nav-search-hover-bg;
        }

        &:active,
        &:focus {
            background-color: hsla(0,0%,39.2%,.15);  // $nav-search-focus-bg;
            color: #fff;  // $nav-search-focus-color;
        }

        &::placeholder {
            color: #ccc;  // $color-menu-text;
        }
    }

    button {
        background-color: transparent;
        position: absolute;
        top: 0;
        right: 1em;
        bottom: 0;
        padding: 0;
        width: 3em;
        transition: right 0.3s ease;

        ${(props) => props.collapsed && css`
            right: 0.5em;
        `}

        &:hover {
            background-color: rgba(100, 100, 100, 0.15);  // $nav-item-hover-bg;
        }

        &:active {
            background-color: #1a1a1a;  // $nav-item-active-bg;
        }

        &:before {
            font-family: wagtail;
            font-weight: 200;
            text-transform: none;
            content: '${getIcon('search') || ''}';
            display: block;
            height: 100%;
            line-height: 3.3em;
            padding: 0 1em;
        }
    }
`;

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
    <SearchForm action={searchUrl} method="get" collapsed={collapsed} visible={isVisible} onSubmit={onSubmitForm}>
      <div>
        <label htmlFor="menu-search-q">{'Search'}</label>{/* GETTEXT */}
        <input type="text" id="menu-search-q" name="q" placeholder={'Search'} />{/* GETTEXT */}
        <button className="button" type="submit">{'Search'}</button>{/* GETTEXT */}
      </div>
    </SearchForm>
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
