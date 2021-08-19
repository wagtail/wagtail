/* global wagtailConfig */

const BULK_ACTION_PAGE_CHECKBOX_INPUT = '[data-bulk-action-checkbox]';
const BULK_ACTION_SELECT_ALL_CHECKBOX = '[data-bulk-action-select-all-checkbox]';
const BULK_ACTIONS_CHECKBOX_PARENT = '[data-bulk-action-parent-id]';
const BULK_ACTION_FILTERS_CLASS = '[data-bulk-action-filter]';
const BULK_ACTION_CHOICES_DIV = '[data-bulk-action-footer]';
const BULK_ACTION_NUM_OBJECTS_SPAN = '[data-bulk-action-num-objects]';
const BULK_ACTION_NUM_OBJECTS_IN_LISTING = '[data-bulk-action-num-objects-in-listing]';

const checkedState = {
  checkedObjects: new Set(),
  numObjects: 0,
  selectAllInListing: false,
  shouldShowAllInListingText: true
};


/**
 * Utility function to get the appropriate string for display in action bar
 */
function getAppropriateStringForListing(key) {
  if (wagtailConfig.BULK_ACTION_ITEM_TYPE in wagtailConfig.STRINGS.BULK_ACTIONS) {
    return wagtailConfig.STRINGS.BULK_ACTIONS[wagtailConfig.BULK_ACTION_ITEM_TYPE][key];
  }
  return wagtailConfig.STRINGS.BULK_ACTIONS.item[key];
}

/**
 * Event listener for the `Select All` checkbox
 */
function onSelectAllChange(e) {
  document.querySelectorAll(`${BULK_ACTION_SELECT_ALL_CHECKBOX}`).forEach(el => {
    el.checked = e.target.checked; // eslint-disable-line no-param-reassign
  });
  const changeEvent = new Event('change');
  for (const el of document.querySelectorAll(`${BULK_ACTION_PAGE_CHECKBOX_INPUT}`)) {
    if (el.checked === e.target.checked) continue;
    el.checked = e.target.checked;
    if (e.target.checked) {
      el.dispatchEvent(changeEvent);
    }
  }
  if (!e.target.checked) {
    // when deselecting all checkbox, simply hide the footer for smooth transition
    checkedState.checkedObjects.clear();
    document.querySelector(`${BULK_ACTION_CHOICES_DIV}`).classList.add('hidden');
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
    document.querySelectorAll(`${BULK_ACTION_SELECT_ALL_CHECKBOX}`).forEach(el => {
      el.checked = false; // eslint-disable-line no-param-reassign
    });
    checkedState.checkedObjects.delete(+e.target.dataset.objectId);
  }

  const numCheckedObjects = checkedState.checkedObjects.size;

  if (numCheckedObjects === 0) {
    /* when all checkboxes are unchecked */
    document.querySelector(`${BULK_ACTION_CHOICES_DIV}`).classList.add('hidden');
    document.querySelectorAll(`${BULK_ACTION_PAGE_CHECKBOX_INPUT}`).forEach(el => el.classList.remove('show'));
  } else if (numCheckedObjects === 1 && prevLength === 0) {
    /* when 1 checkbox is checked for the first time */
    document.querySelectorAll(`${BULK_ACTION_PAGE_CHECKBOX_INPUT}`).forEach(el => {
      el.classList.add('show');
    });
    document.querySelector(`${BULK_ACTION_CHOICES_DIV}`).classList.remove('hidden');
  }

  if (numCheckedObjects === checkedState.numObjects) {
    /* when all checkboxes in the page are checked */
    document.querySelectorAll(`${BULK_ACTION_SELECT_ALL_CHECKBOX}`).forEach(el => {
      el.checked = true; // eslint-disable-line no-param-reassign
    });
    if (checkedState.shouldShowAllInListingText) {
      document.querySelector(`${BULK_ACTION_NUM_OBJECTS_IN_LISTING}`).classList.remove('u-hidden');
    }
  } else if (checkedState.shouldShowAllInListingText) {
    document.querySelector(`${BULK_ACTION_NUM_OBJECTS_IN_LISTING}`).classList.add('u-hidden');
  }

  if (numCheckedObjects > 0) {
    /* Update text on number of pages */
    let numObjectsSelected = '';
    if (numCheckedObjects === 1) {
      numObjectsSelected = getAppropriateStringForListing('SINGULAR');
    } else {
      if (numCheckedObjects === checkedState.numObjects) {
        numObjectsSelected = getAppropriateStringForListing('ALL').replace('{0}', numCheckedObjects);
      } else {
        numObjectsSelected = getAppropriateStringForListing('PLURAL').replace('{0}', numCheckedObjects);
      }
    }
    document.querySelector(`${BULK_ACTION_NUM_OBJECTS_SPAN}`).textContent = numObjectsSelected;
  }
}

/**
 * Event listener to select all objects in listing
 */
function onClickSelectAllInListing(e) {
  e.preventDefault();
  checkedState.selectAllInListing = true;
  document.querySelector(`${BULK_ACTION_NUM_OBJECTS_SPAN}`).
    textContent = `${getAppropriateStringForListing('ALL_IN_LISTING')}.`;
  document.querySelector(`${BULK_ACTION_NUM_OBJECTS_IN_LISTING}`).classList.add('u-hidden');
}

/**
 * Event listener for filter dropdown options
 */
function onClickFilter(e) {
  e.preventDefault();
  const filter = e.target.dataset.bulkActionFilter || '';
  const changeEvent = new Event('change');
  if (filter.length) {
    /* split the filter string into [key,value] pairs and check for the values in the
        BULK_ACTION_PAGE_CHECKBOX_INPUT dataset */
    const [_key, value] = filter.split(':');
    const key = `${_key[0].toUpperCase()}${_key.slice(1)}`;
    for (const el of document.querySelectorAll(`${BULK_ACTION_PAGE_CHECKBOX_INPUT}`)) {
      if (`page${key}` in el.dataset) {
        if (el.dataset[`page${key}`] === value) {
          if (!el.checked) {
            el.checked = true;
            el.dispatchEvent(changeEvent);
          }
        } else {
          if (el.checked) {
            el.checked = false;
            el.dispatchEvent(changeEvent);
          }
        }
      }
    }
  } else {
    /* If filter string is empty, select all checkboxes */
    document.querySelectorAll(`.${BULK_ACTION_SELECT_ALL_CHECKBOX}`).forEach(el => {
      el.checked = true; // eslint-disable-line no-param-reassign
    });
    document.querySelector(`.${BULK_ACTION_SELECT_ALL_CHECKBOX}`).dispatchEvent(changeEvent);
  }
}

/**
 * Event listener for bulk actions which appends selected ids to the corresponding action url
 */
function onClickActionButton(e) {
  e.preventDefault();
  const url = e.target.getAttribute('href');
  const urlParams = new URLSearchParams();
  const parentElement = document.querySelector(`${BULK_ACTIONS_CHECKBOX_PARENT}`);
  if (checkedState.selectAllInListing && parentElement) {
    const parentPageId = parentElement.dataset.bulkActionParentId;
    urlParams.append('id', 'all');
    urlParams.append('childOf', parentPageId);
  } else {
    checkedState.checkedObjects.forEach(objectId => {
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
  document.querySelectorAll(`${BULK_ACTION_PAGE_CHECKBOX_INPUT}`)
    .forEach(el => {
      checkedState.numObjects++;
      el.addEventListener('change', onSelectIndividualCheckbox);
    });
  document.querySelectorAll(`${BULK_ACTION_SELECT_ALL_CHECKBOX}`).forEach(el => {
    el.addEventListener('change', onSelectAllChange);
  });
  document.querySelectorAll(`${BULK_ACTION_FILTERS_CLASS}`).forEach(
    elem => elem.addEventListener('click', onClickFilter)
  );
  document.querySelectorAll(`${BULK_ACTION_CHOICES_DIV} .bulk-action-btn`).forEach(
    elem => elem.addEventListener('click', onClickActionButton)
  );
  const selectAllInListingText = document.querySelector(`${BULK_ACTION_NUM_OBJECTS_IN_LISTING}`);
  if (selectAllInListingText) selectAllInListingText.addEventListener('click', onClickSelectAllInListing);
  else checkedState.shouldShowAllInListingText = false;
  document.querySelectorAll(`${BULK_ACTION_PAGE_CHECKBOX_INPUT}`)
    .forEach(el => {
      if (el.checked) {
        el.dispatchEvent(changeEvent);
      }
    });
}

window.addEventListener('load', addBulkActionListeners);
