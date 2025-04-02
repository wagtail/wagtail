/* global wagtailConfig */

import { range } from '../utils/range';

const BULK_ACTION_PAGE_CHECKBOX_INPUT = '[data-bulk-action-checkbox]';
const BULK_ACTION_SELECT_ALL_CHECKBOX =
  '[data-bulk-action-select-all-checkbox]';
const BULK_ACTIONS_CHECKBOX_PARENT = '[data-bulk-action-parent-id]';
const BULK_ACTION_FOOTER = '[data-bulk-action-footer]';
const BULK_ACTION_NUM_OBJECTS = '[data-bulk-action-num-objects]';
const BULK_ACTION_NUM_OBJECTS_IN_LISTING =
  '[data-bulk-action-num-objects-in-listing]';

/**
 * Get the bulk action item type from the DOM element.
 * This is used to determine the strings to display in the bulk action footer.
 * @type {string}
 */
const BULK_ACTION_ITEM_TYPE = document
  .querySelector(BULK_ACTION_FOOTER)
  .getAttribute('data-bulk-action-footer');
let checkedState = {};

/**
 * Utility function to get the appropriate string for display in action bar
 */
function getStringForListing(key) {
  if (wagtailConfig.STRINGS.BULK_ACTIONS[BULK_ACTION_ITEM_TYPE]) {
    return wagtailConfig.STRINGS.BULK_ACTIONS[BULK_ACTION_ITEM_TYPE][key];
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
    // when deselecting all checkbox, simply hide the footer for smooth transition
    checkedState.checkedObjects.clear();
    document.querySelector(BULK_ACTION_FOOTER).classList.add('hidden');
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
      prevCheckedObjectIndex <= shiftClickedObjectIndex
        ? shiftClickedObjectIndex
        : prevCheckedObjectIndex;

    range(startingIndex, endingIndex).forEach((i) => {
      const changeEvent = new Event('change');
      individualCheckboxList[i].checked =
        individualCheckboxList[prevCheckedObjectIndex].checked;
      individualCheckboxList[i].dispatchEvent(changeEvent);
    });

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
    checkedState.checkedObjects.add(e.target.dataset.objectId);
  } else {
    /* unchecks `Select all` checkbox as soon as one page is unchecked */
    document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach((el) => {
      el.checked = false; // eslint-disable-line no-param-reassign
    });
    checkedState.checkedObjects.delete(e.target.dataset.objectId);
  }

  const numCheckedObjects = checkedState.checkedObjects.size;

  if (numCheckedObjects === 0) {
    document.querySelector(BULK_ACTION_FOOTER).classList.add('hidden');
    document
      .querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT)
      .forEach((el) => el.classList.remove('show'));
  } else if (numCheckedObjects === 1 && prevLength === 0) {
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
        .classList.remove('w-hidden');
    }
  } else if (checkedState.shouldShowAllInListingText) {
    document
      .querySelector(BULK_ACTION_NUM_OBJECTS_IN_LISTING)
      .classList.add('w-hidden');
  }

  if (numCheckedObjects > 0) {
    /* Update text on number of pages */
    let numObjectsSelected = '';
    if (numCheckedObjects === 1) {
      numObjectsSelected = getStringForListing('SINGULAR');
    } else if (numCheckedObjects === checkedState.numObjects) {
      numObjectsSelected = getStringForListing('ALL').replace(
        '%(objects)s',
        numCheckedObjects,
      );
    } else {
      numObjectsSelected = getStringForListing('PLURAL').replace(
        '%(objects)s',
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
  document.querySelector(BULK_ACTION_NUM_OBJECTS).textContent =
    `${getStringForListing('ALL_IN_LISTING')}.`;
  document
    .querySelector(BULK_ACTION_NUM_OBJECTS_IN_LISTING)
    .classList.add('w-hidden');
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
  checkedState = {
    checkedObjects: new Set(),
    numObjects: 0,
    selectAllInListing: false,
    shouldShowAllInListingText: true,
    prevCheckedObject: null,
  };

  const changeEvent = new Event('change');
  document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach((el) => {
    checkedState.numObjects += 1;
    el.addEventListener('change', onSelectIndividualCheckbox);
    el.addEventListener('click', onClickIndividualCheckbox);
  });
  document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach((el) => {
    el.addEventListener('change', onSelectAllChange);
  });
  document
    .querySelectorAll(`${BULK_ACTION_FOOTER} [data-bulk-action-button]`)
    .forEach((elem) => elem.addEventListener('click', onClickActionButton));
  document.addEventListener('w-dropdown:shown', () => {
    document
      .querySelectorAll(`${BULK_ACTION_FOOTER} [data-bulk-action-button]`)
      .forEach((elem) => {
        elem.removeEventListener('click', onClickActionButton);
        elem.addEventListener('click', onClickActionButton);
      });
  });
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
    checkedState.numObjects += 1;
    el.addEventListener('change', onSelectIndividualCheckbox);
  });
}

export { addBulkActionListeners, rebindBulkActionsEventListeners };
