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
    <button type="button" data-bulk-action-num-objects-in-listing class="w-hidden">Select all in listing</button>
    <a href="/admin/bulk/wagtailcore/page/delete/" data-bulk-action-button>Delete</a>
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

describe('bulk-actions action buttons', () => {
  const oldWindowLocation = window.location;
  const listingURL = '/admin/pages/2/?has_child_pages=true&q=hello';

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

  beforeEach(() => {
    delete window.location;
    window.location = { href: `http://localhost${listingURL}` };

    document.body.innerHTML = getHtml();
    const { addBulkActionListeners } = require('./bulk-actions');
    addBulkActionListeners();
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  afterAll(() => {
    window.location = oldWindowLocation;
  });

  it('should send the listing URL when acting on all items in the listing', () => {
    document.getElementById('header-select-all').click();
    document.querySelector('[data-bulk-action-num-objects-in-listing]').click();
    document.querySelector('[data-bulk-action-button]').click();

    const url = new URL(window.location.href);
    expect(url.pathname).toEqual('/admin/bulk/wagtailcore/page/delete/');
    expect(url.searchParams.getAll('id')).toEqual(['all']);
    expect(url.searchParams.get('listing_url')).toEqual(listingURL);
    expect(url.searchParams.get('next')).toEqual(listingURL);
  });

  it('should only send the selected ids when acting on selected items', () => {
    document.querySelector("[data-object-id='45']").click();
    document.querySelector('[data-bulk-action-button]').click();

    const url = new URL(window.location.href);
    expect(url.pathname).toEqual('/admin/bulk/wagtailcore/page/delete/');
    expect(url.searchParams.getAll('id')).toEqual(['45']);
    expect(url.searchParams.has('listing_url')).toBe(false);
    expect(url.searchParams.get('next')).toEqual(listingURL);
  });
});
