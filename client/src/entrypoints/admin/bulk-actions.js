/* global wagtailConfig */

const BULK_ACTION_PAGE_CHECKBOX_INPUT = '[data-bulk-action-checkbox]';
const BULK_ACTION_SELECT_ALL_CHECKBOX =
  '[data-bulk-action-select-all-checkbox]';
const BULK_ACTIONS_CHECKBOX_PARENT = '[data-bulk-action-parent-id]';
const BULK_ACTION_FOOTER = '[data-bulk-action-footer]';
const BULK_ACTION_NUM_OBJECTS = '[data-bulk-action-num-objects]';
const BULK_ACTION_NUM_OBJECTS_IN_LISTING =
  '[data-bulk-action-num-objects-in-listing]';
const MORE_ACTIONS_DROPDOWN_BUTTON_SELECTOR = '.actions [data-dropdown]';

const checkedState = {
  checkedObjects: new Set(),
  numObjects: 0,
  selectAllInListing: false,
  shouldShowAllInListingText: true,
  prevCheckedObject: null,
};

/**
 * Toggles the 'more' dropdown button in listing pages.
 * @param {boolean} show - Determines if the button should be shown or not.
 */
function toggleMoreActionsDropdownBtn(show) {
  const moreActionsDropdown = document.querySelector(
    MORE_ACTIONS_DROPDOWN_BUTTON_SELECTOR,
  );
  if (moreActionsDropdown !== null) {
    if (show === true) {
      moreActionsDropdown.classList.remove('hidden');
    } else {
      moreActionsDropdown.classList.add('hidden');
    }
  }
}

/**
 * Utility function to get the appropriate string for display in action bar
 */
function getStringForListing(key) {
  if (wagtailConfig.STRINGS.BULK_ACTIONS[wagtailConfig.BULK_ACTION_ITEM_TYPE]) {
    return wagtailConfig.STRINGS.BULK_ACTIONS[
      wagtailConfig.BULK_ACTION_ITEM_TYPE
    ][key];
  }
  return wagtailConfig.STRINGS.BULK_ACTIONS.ITEM[key];
}

/**
 * Event listener for the `Select All` checkbox
 */
function onSelectAllChange(e) {
  document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach((el) => {
    el.checked = e.target.checked; // eslint-disable-line no-param-reassign
  });
  const changeEvent = new Event('change');
  document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach((el) => {
    if (el.checked !== e.target.checked) {
      // eslint-disable-next-line no-param-reassign
      el.checked = e.target.checked;
      if (e.target.checked) {
        el.dispatchEvent(changeEvent);
      } else {
        el.classList.remove('show');
      }
    }
  });
  if (!e.target.checked) {
    toggleMoreActionsDropdownBtn(true);
    // when deselecting all checkbox, simply hide the footer for smooth transition
    checkedState.checkedObjects.clear();
    document.querySelector(BULK_ACTION_FOOTER).classList.add('hidden');
  } else {
    toggleMoreActionsDropdownBtn(false);
  }
}

/**
 * Event listener for clicking individual checkbox and checking if shift key is pressed
 *
 * @param {Event} event
 */
function onClickIndividualCheckbox(event) {
  if (event.shiftKey && checkedState.prevCheckedObject) {
    const individualCheckboxList = [
      ...document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT),
    ];
    const prevCheckedObjectIndex = individualCheckboxList.findIndex(
      (el) => el.dataset.objectId === checkedState.prevCheckedObject,
    );
    const shiftClickedObjectIndex = individualCheckboxList.findIndex(
      (el) => el.dataset.objectId === event.target.dataset.objectId,
    );

    const startingIndex =
      (prevCheckedObjectIndex > shiftClickedObjectIndex
        ? shiftClickedObjectIndex
        : prevCheckedObjectIndex) + 1;
    const endingIndex =
      (prevCheckedObjectIndex <= shiftClickedObjectIndex
        ? shiftClickedObjectIndex
        : prevCheckedObjectIndex) - 1;

    for (let i = startingIndex; i <= endingIndex; i++) {
      const changeEvent = new Event('change');
      individualCheckboxList[i].checked =
        individualCheckboxList[prevCheckedObjectIndex].checked;
      individualCheckboxList[i].dispatchEvent(changeEvent);
    }
    checkedState.prevCheckedObject = event.target.dataset.objectId;
  }
}

/**
 * Event listener for individual checkbox
 */
function onSelectIndividualCheckbox(e) {
  if (checkedState.selectAllInListing) checkedState.selectAllInListing = false;
  const prevLength = checkedState.checkedObjects.size;
  if (e.target.checked) {
    checkedState.checkedObjects.add(Number(e.target.dataset.objectId));
  } else {
    /* unchecks `Select all` checkbox as soon as one page is unchecked */
    document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach((el) => {
      el.checked = false; // eslint-disable-line no-param-reassign
    });
    checkedState.checkedObjects.delete(Number(e.target.dataset.objectId));
  }

  const numCheckedObjects = checkedState.checkedObjects.size;

  if (numCheckedObjects === 0) {
    /* when all checkboxes are unchecked */
    toggleMoreActionsDropdownBtn(true);
    document.querySelector(BULK_ACTION_FOOTER).classList.add('hidden');
    document
      .querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT)
      .forEach((el) => el.classList.remove('show'));
  } else if (numCheckedObjects === 1 && prevLength === 0) {
    /* when 1 checkbox is checked for the first time */
    toggleMoreActionsDropdownBtn(false);
    document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach((el) => {
      el.classList.add('show');
    });
    document.querySelector(BULK_ACTION_FOOTER).classList.remove('hidden');
  }

  if (numCheckedObjects === checkedState.numObjects) {
    /* when all checkboxes in the page are checked */
    document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach((el) => {
      el.checked = true; // eslint-disable-line no-param-reassign
    });
    if (checkedState.shouldShowAllInListingText) {
      document
        .querySelector(BULK_ACTION_NUM_OBJECTS_IN_LISTING)
        .classList.remove('u-hidden');
    }
  } else if (checkedState.shouldShowAllInListingText) {
    document
      .querySelector(BULK_ACTION_NUM_OBJECTS_IN_LISTING)
      .classList.add('u-hidden');
  }

  if (numCheckedObjects > 0) {
    /* Update text on number of pages */
    let numObjectsSelected = '';
    if (numCheckedObjects === 1) {
      numObjectsSelected = getStringForListing('SINGULAR');
    } else if (numCheckedObjects === checkedState.numObjects) {
      numObjectsSelected = getStringForListing('ALL').replace(
        '{0}',
        numCheckedObjects,
      );
    } else {
      numObjectsSelected = getStringForListing('PLURAL').replace(
        '{0}',
        numCheckedObjects,
      );
    }
    document.querySelector(BULK_ACTION_NUM_OBJECTS).textContent =
      numObjectsSelected;
  }

  // Updating previously checked object
  checkedState.prevCheckedObject = e.target.dataset.objectId;
}

/**
 * Event listener to select all objects in listing
 */
function onClickSelectAllInListing(e) {
  e.preventDefault();
  checkedState.selectAllInListing = true;
  document.querySelector(
    BULK_ACTION_NUM_OBJECTS,
  ).textContent = `${getStringForListing('ALL_IN_LISTING')}.`;
  document
    .querySelector(BULK_ACTION_NUM_OBJECTS_IN_LISTING)
    .classList.add('u-hidden');
}

/**
 * Event listener for bulk actions which appends selected ids to the corresponding action url
 */
function onClickActionButton(e) {
  e.preventDefault();
  const url = e.target.getAttribute('href');
  const urlParams = new URLSearchParams(window.location.search);
  if (checkedState.selectAllInListing) {
    urlParams.append('id', 'all');
    const parentElement = document.querySelector(BULK_ACTIONS_CHECKBOX_PARENT);
    if (parentElement) {
      const parentPageId = parentElement.dataset.bulkActionParentId;
      urlParams.append('childOf', parentPageId);
    }
  } else {
    checkedState.checkedObjects.forEach((objectId) => {
      urlParams.append('id', objectId);
    });
  }
  window.location.href = `${url}&${urlParams.toString()}`;
}

/**
 * Adds all event listeners
 */
function addBulkActionListeners() {
  const changeEvent = new Event('change');
  document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach((el) => {
    checkedState.numObjects++;
    el.addEventListener('change', onSelectIndividualCheckbox);
    el.addEventListener('click', onClickIndividualCheckbox);
  });
  document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach((el) => {
    el.addEventListener('change', onSelectAllChange);
  });
  document
    .querySelectorAll(`${BULK_ACTION_FOOTER} .bulk-action-btn`)
    .forEach((elem) => elem.addEventListener('click', onClickActionButton));
  const selectAllInListingText = document.querySelector(
    BULK_ACTION_NUM_OBJECTS_IN_LISTING,
  );
  if (selectAllInListingText)
    selectAllInListingText.addEventListener('click', onClickSelectAllInListing);
  else checkedState.shouldShowAllInListingText = false;
  document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach((el) => {
    if (el.checked) {
      el.dispatchEvent(changeEvent);
    }
  });
}

function rebindBulkActionsEventListeners() {
  // when deselecting all checkbox, simply hide the footer for smooth transition
  document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach((el) => {
    el.checked = false; // eslint-disable-line no-param-reassign
  });
  document.querySelector(BULK_ACTION_FOOTER).classList.add('hidden');
  document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach((el) => {
    // remove already attached event listener first
    el.removeEventListener('change', onSelectAllChange);
    el.addEventListener('change', onSelectAllChange);
  });
  checkedState.checkedObjects.clear();
  checkedState.numObjects = 0;
  document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach((el) => {
    checkedState.numObjects++;
    el.addEventListener('change', onSelectIndividualCheckbox);
  });
}

document.addEventListener('DOMContentLoaded', addBulkActionListeners);
if (window.headerSearch) {
  const termInput = document.querySelector(window.headerSearch.termInput);
  if (termInput) {
    termInput.addEventListener(
      'search-success',
      rebindBulkActionsEventListeners,
    );
  }
}
