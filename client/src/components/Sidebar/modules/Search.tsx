import * as React from 'react';

import Tippy from '@tippyjs/react';
import { gettext } from '../../../utils/gettext';
import Icon from '../../Icon/Icon';
import { ModuleDefinition, SIDEBAR_TRANSITION_DURATION } from '../Sidebar';

interface SearchInputProps {
  slim: boolean;
  expandingOrCollapsing: boolean;
  onSearchClick: () => void;
  searchUrl: string;
  navigate(url: string): void;
}

export const SearchInput: React.FunctionComponent<SearchInputProps> = ({
  slim,
  expandingOrCollapsing,
  onSearchClick,
  searchUrl,
  navigate,
}) => {
  const isVisible = !slim || expandingOrCollapsing;
  const searchInput = React.useRef<HTMLInputElement>(null);

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

  return (
    <form
      role="search"
      className="w-h-[42px] w-relative w-box-border w-flex w-items-center w-justify-start w-flex-row w-flex-shrink-0"
      action={searchUrl}
      method="get"
      onSubmit={onSubmitForm}
    >
      <div className="w-flex w-flex-row w-items-center w-h-full">
        <Tippy
          disabled={isVisible || !slim}
          content={gettext('Search')}
          placement="right"
        >
          {/* Use padding left 23px to align icon in slim mode and padding right 18px to ensure focus is full width */}
          <button
            className={`
          ${slim ? 'w-pr-[18px]' : 'w-pr-0'}
          w-w-full
          w-pl-[23px]
          w-h-[35px]
          w-bg-transparent
          w-outline-offset-inside
          w-border-0
          w-rounded-none
          w-text-white/80
          w-z-10
          hover:w-text-white
          focus:w-text-white
          hover:w-bg-transparent`}
            type="submit"
            aria-label={gettext('Search')}
            onClick={(e) => {
              if (slim) {
                e.preventDefault();
                onSearchClick();

                // Focus search input after transition when button is clicked in slim mode
                setTimeout(() => {
                  if (searchInput.current) {
                    searchInput.current.focus();
                  }
                }, SIDEBAR_TRANSITION_DURATION);
              }
            }}
          >
            <Icon className="icon--menuitem" name="search" />
          </button>
        </Tippy>

        <label className="w-sr-only" htmlFor="menu-search-q">
          {gettext('Search')}
        </label>

        {/* Classes marked important to trump the base input styling set in _forms.scss */}
        <input
          className={`
            ${slim || !isVisible ? 'w-hidden' : ''}
            !w-pl-[55px]
            !w-py-[13px]
            !w-subpixel-antialiased
            !w-absolute
            !w-left-0
            !w-font-normal
            !w-top-0
            !w-text-14
            !w-bg-transparent
            !w-border-0
            !w-rounded-none
            !w-text-white/80
            !w-outline-offset-inside
            !w-leading-none
            placeholder:!w-text-white/80`}
          type="text"
          id="menu-search-q"
          name="q"
          placeholder={gettext('Search')}
          ref={searchInput}
        />
      </div>
    </form>
  );
};

export class SearchModuleDefinition implements ModuleDefinition {
  searchUrl: string;

  constructor(searchUrl: string) {
    this.searchUrl = searchUrl;
  }

  render({ slim, key, expandingOrCollapsing, onSearchClick, navigate }) {
    return (
      <SearchInput
        searchUrl={this.searchUrl}
        slim={slim}
        key={key}
        expandingOrCollapsing={expandingOrCollapsing}
        onSearchClick={onSearchClick}
        navigate={navigate}
      />
    );
  }
}
