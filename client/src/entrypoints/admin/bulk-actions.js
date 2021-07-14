/* global wagtailConfig */

const BULK_ACTION_PAGE_CHECKBOX_INPUT = 'bulk-action-checkbox';
const BULK_ACTION_SELECT_ALL_CHECKBOX_TH = 'bulk-actions-filter-checkbox';
const BULK_ACTION_FILTERS_CLASS = `${BULK_ACTION_SELECT_ALL_CHECKBOX_TH} .c-dropdown__item a`;
const BULK_ACTION_CHOICES_DIV = 'bulk-actions-choices';
const BULK_ACTION_NUM_PAGES_SPAN = 'num-pages';
const BULK_ACTION_NUM_PAGES_IN_LISTING = 'num-pages-in-listing';

const checkedState = {
  checkedPages: new Set(),
  numPages: 0,
  selectAllInListing: false,
  shouldShowAllInListingText: true
};

/* Event listener for the `Select All` checkbox */
function SelectBulkActionsFilter(e) {
  const changeEvent = new Event('change');
  for (const el of document.querySelectorAll(`.${BULK_ACTION_PAGE_CHECKBOX_INPUT}`)) {
    if (el.checked === e.target.checked) continue;
    el.checked = e.target.checked;
    el.dispatchEvent(changeEvent);
  }
}


/* Event listener for individual page checkbox */
function SelectBulkActionsCheckboxes(e) {
  if (checkedState.selectAllInListing) checkedState.selectAllInListing = false;
  const prevLength = checkedState.checkedPages.size;
  if (e.target.checked) checkedState.checkedPages.add(+e.target.dataset.pageId);
  else {
    /* unchecks `Select all` checkbox as soon as one page is unchecked */
    document.querySelectorAll(`.${BULK_ACTION_SELECT_ALL_CHECKBOX_TH} input`).forEach(_el => {
      const el = _el;
      el.checked = false;
    });
    checkedState.checkedPages.delete(+e.target.dataset.pageId);
  }

  if (checkedState.checkedPages.size === 0) {
    /* when all checkboxes are unchecked */
    document.querySelector(`.${BULK_ACTION_CHOICES_DIV}`).classList.add('hidden');
    document.querySelectorAll(`.${BULK_ACTION_PAGE_CHECKBOX_INPUT}`).forEach(el => el.classList.remove('show'));
  } else if (checkedState.checkedPages.size === 1 && prevLength === 0) {
    /* when 1 checkbox is checked for the first time */
    document.querySelectorAll(`.${BULK_ACTION_PAGE_CHECKBOX_INPUT}`).forEach(el => {
      el.classList.add('show');
    });
    document.querySelector(`.${BULK_ACTION_CHOICES_DIV}`).classList.remove('hidden');
  }

  if (checkedState.checkedPages.size === checkedState.numPages) {
    /* when all checkboxes in the page are checked */
    document.querySelectorAll(`.${BULK_ACTION_SELECT_ALL_CHECKBOX_TH} input`).forEach(_el => {
      const el = _el;
      el.checked = true;
    });
  }

  if (checkedState.checkedPages.size > 0) {
    /* Update text on number of pages */
    let numPagesSelected = '';
    const numCheckPages = checkedState.checkedPages.size;
    if (numCheckPages === 1) {
      numPagesSelected = wagtailConfig.STRINGS.NUM_PAGES_SELECTED_SINGULAR;
    } else {
      if (numCheckPages === checkedState.numPages) {
        numPagesSelected = wagtailConfig.STRINGS.NUM_PAGES_SELECTED_ALL.replace('{0}', numCheckPages);
      } else {
        numPagesSelected = wagtailConfig.STRINGS.NUM_PAGES_SELECTED_PLURAL.replace('{0}', numCheckPages);
      }
    }
    document.querySelector(`.${BULK_ACTION_NUM_PAGES_IN_LISTING}`).classList.add('u-hidden');
    document.querySelector(`.${BULK_ACTION_NUM_PAGES_SPAN}`).textContent = numPagesSelected;
  }
}

function selectAllPageIdsInListing() {
  checkedState.selectAllInListing = true;
  document.querySelector(`.${BULK_ACTION_NUM_PAGES_SPAN}`).
    textContent = wagtailConfig.STRINGS.NUM_PAGES_SELECTED_ALL_IN_LISTING + '.';
  document.querySelector(`.${BULK_ACTION_NUM_PAGES_IN_LISTING}`).classList.add('u-hidden');
}

/* Event listener for filter dropdown options */
function FilterEventListener(e) {
  e.preventDefault();
  const filter = e.target.dataset.filter || '';
  const changeEvent = new Event('change');
  if (filter.length) {
    /* split the filter string into [key,value] pairs and check for the values in the
        BULK_ACTION_PAGE_CHECKBOX_INPUT dataset */
    const [_key, value] = filter.split(':');
    const key = _key[0].toUpperCase() + _key.slice(1);
    for (const el of document.querySelectorAll(`.${BULK_ACTION_PAGE_CHECKBOX_INPUT}`)) {
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
    document.querySelectorAll(`.${BULK_ACTION_SELECT_ALL_CHECKBOX_TH}`).forEach(_el => {
      const el = _el;
      el.checked = true;
    });
    document.querySelector(`.${BULK_ACTION_SELECT_ALL_CHECKBOX_TH}`).dispatchEvent(changeEvent);
  }
}

/* Event listener for bulk actions which appends selected page ids to the corresponding action url */
function BulkActionEventListeners(e) {
  e.preventDefault();
  const url = e.target.getAttribute('href');
  let queryString = '';
  if (checkedState.selectAllInListing) {
    const parentPageId = document.querySelector(`.${BULK_ACTION_SELECT_ALL_CHECKBOX_TH}`).dataset.parentId;
    queryString += `&id=all&childOf=${parentPageId}`;
  } else {
    checkedState.checkedPages.forEach(pageId => {
      queryString += `&id=${pageId}`;
    });
  }
  window.location.href = url + queryString;
}


/* Adds all event listeners */
function addBulkActionListeners() {
  document.querySelectorAll(`.${BULK_ACTION_PAGE_CHECKBOX_INPUT}`)
    .forEach(el => {
      checkedState.numPages++;
      el.addEventListener('change', SelectBulkActionsCheckboxes);
    });
  document.querySelectorAll(`.${BULK_ACTION_SELECT_ALL_CHECKBOX_TH} input`).forEach(el => {
    el.addEventListener('change', SelectBulkActionsFilter);
  });
  document.querySelectorAll(`.${BULK_ACTION_FILTERS_CLASS}`).forEach(
    elem => elem.addEventListener('click', FilterEventListener)
  );
  document.querySelectorAll(`.${BULK_ACTION_CHOICES_DIV} ul > li > a`).forEach(
    elem => elem.addEventListener('click', BulkActionEventListeners)
  );
  const selectAllInListingText = document.querySelector(`.${BULK_ACTION_NUM_PAGES_IN_LISTING}`);
  if (selectAllInListingText) selectAllInListingText.addEventListener('click', selectAllPageIdsInListing);
  else checkedState.shouldShowAllInListingText = false;
}

addBulkActionListeners();
