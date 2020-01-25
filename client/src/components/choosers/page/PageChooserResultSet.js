import React, { useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';

import { STRINGS } from '../../../config/wagtailConfig';

import PageChooserPagination from './PageChooserPagination';
import PageChooserResult from './PageChooserResult';

function pageIsNavigable(displayChildNavigation, page) {
  return displayChildNavigation && page.meta.children.count > 0;
}

function pageIsChoosable(restrictPageTypes, page) {
  if (restrictPageTypes != null && restrictPageTypes.indexOf(page.meta.type.toLowerCase()) === -1) {
    return false;
  }

  return true;
}

const propTypes = {
  displayChildNavigation: PropTypes.bool,
  restrictPageTypes: PropTypes.array,
  items: PropTypes.array,
  onPageChosen: PropTypes.func.isRequired,
  onNavigate: PropTypes.func.isRequired,
  pageTypes: PropTypes.object,
  parentPage: PropTypes.any,
  pageNumber: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  onChangePage: PropTypes.func.isRequired,
  keydownEventHandlerRef: PropTypes.object,
};

const defaultProps = {
  displayChildNavigation: false,
  restrictPageTypes: [],
  items: [],
  pageTypes: {},
  parentPage: null,
};

function PageChooserResultSet(props) {
  const { items,
    onPageChosen,
    onNavigate,
    pageTypes,
    parentPage,
    pageNumber,
    totalPages,
    onChangePage,
    keydownEventHandlerRef } = props;

  // Focused item
  // This stores which of the items on the page are in focus.
  // Can have one of the following values:
  // - null = Nothing is focused yet
  // - page-<id> = A page
  // - 'pagination' = The pagination UI at the bottom is focused
  const [focusedItem, setFocusedItem] = useState(null);

  // Recalculate focusable items whenever things change
  const focusableItems = useMemo(() => {
    const theFocusableItems = [];
    if (parentPage) {
      theFocusableItems.push(`page-${parentPage.id}`);
    }

    items.forEach(page => {
      theFocusableItems.push(`page-${page.id}`);
    });

    if (totalPages > 1) {
      theFocusableItems.push('pagination');
    }

    return theFocusableItems;
  }, [parentPage, items, totalPages]);

  // If the currently focused item is no longer focusable, unfocus it
  useEffect(() => {
    if (focusedItem && focusableItems.indexOf(focusedItem) === -1) {
      setFocusedItem(null);
    }
  }, [focusableItems]);

  keydownEventHandlerRef.current = e => {
    if (e.key === 'ArrowDown') {
      if (focusedItem === null) {
        // Set focus to the first item
        if (focusableItems) {
          setFocusedItem(focusableItems[0]);
        }
      } else {
        // Set focus to the next item

        // Note, if the item isn't in the array for some reason, this will be 0
        // Which just happens to be the behaviour we want
        let newIndex = focusableItems.indexOf(focusedItem) + 1;

        if (newIndex >= focusableItems.length) {
          newIndex = 0;
        }

        if (focusableItems) {
          setFocusedItem(focusableItems[newIndex]);
        }
      }

      e.preventDefault();
    }

    if (e.key === 'ArrowUp') {
      if (focusedItem === null) {
        // Set focus to the last item
        if (focusableItems) {
          setFocusedItem(focusableItems[focusableItems.length - 1]);
        }
      } else {
        // Set focus to the previous item

        // Note, if the item isn't in the array for some reason, this will be 0
        let newIndex = focusableItems.indexOf(focusedItem) - 1;

        if (newIndex < 0) {
          newIndex = focusableItems.length - 1;
        }

        if (focusableItems) {
          setFocusedItem(focusableItems[newIndex]);
        }
      }

      e.preventDefault();
    }

    if (e.key === 'ArrowRight') {
      if (focusedItem === 'pagination') {
        if (pageNumber < totalPages) {
          onChangePage(pageNumber + 1);
        }
      } else if (focusedItem !== null) {
        const page = items.filter(item => `page-${item.id}` === focusedItem);

        if (page.length > 0) {
          if (pageIsNavigable(props.displayChildNavigation, page[0])) {
            onNavigate(page[0]);
          }
        }
      }

      e.preventDefault();
    }

    if (e.key === 'ArrowLeft') {
      if (focusedItem === 'pagination') {
        if (pageNumber > 1) {
          onChangePage(pageNumber - 1);
        }
      } else if (parentPage) {
        const ancestors = parentPage.meta.ancestors;

        if (ancestors.length > 0) {
          onNavigate(ancestors[ancestors.length - 1]);
          setFocusedItem(`page-${parentPage.id}`);
        }
      }
    }

    if (e.key === 'Enter') {
      if (focusedItem !== null) {
        const page = items.filter(item => `page-${item.id}` === focusedItem);

        if (page.length > 0) {
          if (pageIsChoosable(props.restrictPageTypes, page[0])) {
            onPageChosen(page[0]);
          }
        }
      }

      e.preventDefault();
    }
  };

  const results = items.map((page, i) => {
    const onChoose = (e) => {
      onPageChosen(page);
      e.preventDefault();
    };

    const handleNavigate = (e) => {
      onNavigate(page);
      e.preventDefault();
    };

    return (
      <PageChooserResult
        key={i}
        page={page}
        isChoosable={pageIsChoosable(props.restrictPageTypes, page)}
        isNavigable={pageIsNavigable(props.displayChildNavigation, page)}
        isFocused={focusedItem === `page-${page.id}`}
        onChoose={onChoose}
        onNavigate={handleNavigate}
        pageTypes={pageTypes}
      />
    );
  });

  // Parent page
  let parent = null;

  if (parentPage) {
    const onChoose = (e) => {
      onPageChosen(parentPage);
      e.preventDefault();
    };

    const handleNavigate = (e) => {
      onNavigate(parentPage);
      e.preventDefault();
    };

    parent = (
      <PageChooserResult
        page={parentPage}
        isParent={true}
        isChoosable={pageIsChoosable(props.restrictPageTypes, parentPage)}
        isNavigable={false}
        isFocused={focusedItem === `page-${parentPage.id}`}
        onChoose={onChoose}
        onNavigate={handleNavigate}
        pageTypes={pageTypes}
      />
    );
  }

  return (
    <div className="page-results">
      <table className="listing  chooser">
        <colgroup>
          <col />
          <col width="12%" />
          <col width="12%" />
          <col width="12%" />
          <col width="10%" />
        </colgroup>
        <thead>
          <tr className="table-headers">
            <th className="title">{STRINGS.TITLE}</th>
            <th className="updated">{STRINGS.UPDATED}</th>
            <th className="type">{STRINGS.TYPE}</th>
            <th className="status">{STRINGS.STATUS}</th>
            <th />
          </tr>
          {parent}
        </thead>
        <tbody>
          {results}
        </tbody>
      </table>

      <PageChooserPagination
        pageNumber={pageNumber}
        totalPages={totalPages}
        onChangePage={onChangePage}
        isFocused={focusedItem === 'pagination'}
      />
    </div>
  );
}

PageChooserResultSet.propTypes = propTypes;
PageChooserResultSet.defaultProps = defaultProps;

export default PageChooserResultSet;
