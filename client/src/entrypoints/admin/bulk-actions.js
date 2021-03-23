const BULK_ACTION_CHECKBOX_CLASS = 'bulk-action-checkbox';
const BULK_ACTION_CHECKBOX_FILTER_CLASS = 'bulk-actions-filter-checkbox';
const BULK_ACTION_CHOICES_CLASS = 'bulk-actions-choices';
const TABLE_HEADERS_CLASS = 'table-headers';

const checkedState = {
  checkedPages: new Set(),
};

function SelectBulkActionsFilter(e) {
  const changeEvent = new Event('change');
  for (const el of document.querySelectorAll(`.${BULK_ACTION_CHECKBOX_CLASS}`)) {
    if (el.checked === e.target.checked) continue;
    el.checked = e.target.checked;
    el.dispatchEvent(changeEvent);
  }
}

function SelectBulkActionsCheckboxes(e) {
  const prevLength = checkedState.checkedPages.size;
  if (e.target.checked) checkedState.checkedPages.add(+e.target.dataset.pageId);
  else {
    // unchecks `select all` checkbox as soon as one page is unchecked
    document.querySelector(`.${BULK_ACTION_CHECKBOX_FILTER_CLASS} input`).checked = false;
    checkedState.checkedPages.delete(+e.target.dataset.pageId);
  }

  if (checkedState.checkedPages.size === 0) {
    // all checboxes are unchecked
    document.querySelectorAll(`.${TABLE_HEADERS_CLASS} > th`).forEach(el => el.classList.remove('u-hidden'));
    document.querySelector(`.${BULK_ACTION_CHOICES_CLASS}`).classList.add('u-hidden');
    document.querySelectorAll(`.${BULK_ACTION_CHECKBOX_CLASS}`).forEach(el => el.classList.remove('show'));
    document.querySelector(`.${BULK_ACTION_CHECKBOX_FILTER_CLASS}`).setAttribute('colspan', '1');
  } else if (checkedState.checkedPages.size === document.querySelectorAll(`.${BULK_ACTION_CHECKBOX_CLASS}`).length) {
    // all checkboxes are checked
    document.querySelector(`.${BULK_ACTION_CHECKBOX_FILTER_CLASS} input`).checked = true;
  } else if (checkedState.checkedPages.size === 1 && prevLength === 0) {
    // 1 checkbox is checked for the first time
    document.querySelectorAll(`.${BULK_ACTION_CHECKBOX_CLASS}`).forEach(el => {
      el.classList.remove('show');
      el.classList.add('show');
    });
    document.querySelectorAll(`.${TABLE_HEADERS_CLASS} > th`).forEach(el => el.classList.add('u-hidden'));
    document.querySelector(`.${BULK_ACTION_CHECKBOX_FILTER_CLASS}`).classList.remove('u-hidden');
    document.querySelector(`.${BULK_ACTION_CHOICES_CLASS}`).classList.remove('u-hidden');
    document.querySelector(`.${BULK_ACTION_CHECKBOX_FILTER_CLASS}`).setAttribute('colspan', '6');
  }
}

function AddBulkActionCheckboxEventListeners() {
  document.querySelectorAll(`.${BULK_ACTION_CHECKBOX_CLASS}`)
    .forEach(el => el.addEventListener('change', SelectBulkActionsCheckboxes));
  document.querySelector(`.${BULK_ACTION_CHECKBOX_FILTER_CLASS}`).addEventListener('change', SelectBulkActionsFilter);
}

window.AddBulkActionCheckboxEventListeners = AddBulkActionCheckboxEventListeners;
