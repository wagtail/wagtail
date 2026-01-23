const getHtml = ({ objectIds = [1, 45, 23, 'uuid-1', 'uuid-2'] } = {}) => `
<main>
  <input data-bulk-action-select-all-checkbox type="checkbox" id="header-select-all"/>
  <div class="listing">
  ${objectIds
    .map(
      (id) =>
        `<input type="checkbox" data-object-id="${id}" data-bulk-action-checkbox class="bulk-action-checkbox" />`,
    )
    .join('')}
  </div>
  <footer class="footer bulk-actions-choices hidden" data-bulk-action-footer="PAGE">
    <input data-bulk-action-select-all-checkbox type="checkbox" id="footer-select-all"/>
    <span data-bulk-action-num-objects class="num-objects"></span>
  </footer>
</main>
`;

describe('bulk-actions', () => {
  beforeAll(() => {
    window.wagtailConfig = {
      STRINGS: {
        BULK_ACTIONS: {
          PAGE: {
            ALL_IN_LISTING: 'ALL_IN_LISTING',
            ALL: 'ALL',
            PLURAL: 'PLURAL',
            SINGULAR: 'SINGULAR',
          },
        },
      },
    };
  });

  afterEach(() => {
    // clean up DOM
    document.body.innerHTML = '';
    document.head.innerHTML = '';
  });

  beforeEach(() => {
    document.body.innerHTML = getHtml();

    // import after globals (strings) are created
    const { addBulkActionListeners } = require('./bulk-actions');

    // connect listeners
    addBulkActionListeners();

    // unchecked by default
    expect(document.querySelectorAll('.bulk-action-checkbox')).toHaveLength(5);
    document.querySelectorAll('.bulk-action-checkbox').forEach((input) => {
      expect(input.checked).toBe(false);
    });

    // footer should be hidden (by default)
    expect(
      document.querySelector('footer').classList.contains('hidden'),
    ).toEqual(true);
  });

  it('should check any select all checkboxes if each item is checked individually', () => {
    expect(document.querySelectorAll('.bulk-action-checkbox')).toHaveLength(5);

    // check all items individually
    document.querySelectorAll('.bulk-action-checkbox').forEach((input) => {
      expect(input.checked).toBe(false);
      input.click();
      expect(input.checked).toBe(true);
    });

    // any select all checkboxes should now be checked
    expect(document.getElementById('header-select-all').checked).toBe(true);
    expect(document.getElementById('footer-select-all').checked).toBe(true);

    // footer should now be visible
    expect(
      document.querySelector('footer').classList.contains('hidden'),
    ).toEqual(false);
  });

  it('should check all checkboxes when select all is clicked and show the footer', () => {
    // select all in header (click)
    document.getElementById('header-select-all').click();

    // all should be checked
    expect(document.querySelectorAll('.bulk-action-checkbox')).toHaveLength(5);
    document.querySelectorAll('.bulk-action-checkbox').forEach((input) => {
      expect(input.checked).toBe(true);
    });

    // footer should be visible
    expect(
      document.querySelector('footer').classList.contains('hidden'),
    ).toEqual(false);
  });

  it('should unselect all checkboxes when select all in footer is clicked & hide the footer', () => {
    // select all in header (click)
    document.getElementById('header-select-all').click();

    // all should be checked
    expect(document.querySelectorAll('.bulk-action-checkbox')).toHaveLength(5);
    document.querySelectorAll('.bulk-action-checkbox').forEach((input) => {
      expect(input.checked).toBe(true);
    });

    document.getElementById('footer-select-all').click();

    // all should be unchecked
    expect(document.querySelectorAll('.bulk-action-checkbox')).toHaveLength(5);
    document.querySelectorAll('.bulk-action-checkbox').forEach((input) => {
      expect(input.checked).toBe(false);
    });

    // footer should be hidden
    expect(
      document.querySelector('footer').classList.contains('hidden'),
    ).toEqual(true);
  });

  it('should un-check the select all checkboxes one checkbox is individually unchecked', () => {
    // select all in header (click)
    document.getElementById('header-select-all').click();

    // all should be checked
    expect(document.querySelectorAll('.bulk-action-checkbox')).toHaveLength(5);
    document.querySelectorAll('.bulk-action-checkbox').forEach((input) => {
      expect(input.checked).toBe(true);
    });

    // uncheck one checkbox
    const checkbox = document.querySelector("[data-object-id='uuid-1']");
    expect(checkbox.checked).toBe(true);
    checkbox.click();
    expect(checkbox.checked).toBe(false);

    // any select all checkboxes should now be unchecked
    expect(document.getElementById('header-select-all').checked).toBe(false);
    expect(document.getElementById('footer-select-all').checked).toBe(false);

    // footer should still be visible as only one item unchecked
    expect(
      document.querySelector('footer').classList.contains('hidden'),
    ).toEqual(false);
  });
});
