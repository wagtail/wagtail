import { Application } from '@hotwired/stimulus';
import { BulkController } from './BulkController';

describe('BulkController', () => {
  beforeEach(() => {
    document.body.innerHTML = `
    <div data-controller="w-bulk">
      <input id="select-all" type="checkbox" data-w-bulk-target="all" data-action="w-bulk#toggleAll">
      <div id="checkboxes">
        <input type="checkbox" data-w-bulk-target="item" disabled data-action="w-bulk#toggle">
        <input type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
        <input type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
      </div>
      <button id="clear" data-action="w-bulk#toggleAll" data-w-bulk-force-param="false">Clear all</button>
      <button id="set" data-action="w-bulk#toggleAll" data-w-bulk-force-param="true">Select all</button>
    </div>
    `;
    const application = Application.start();
    application.register('w-bulk', BulkController);
  });

  it('selects all checkboxes when the select all checkbox is clicked', () => {
    const allCheckbox = document.getElementById('select-all');

    allCheckbox.click();

    expect(
      document
        .getElementById('checkboxes')
        .querySelectorAll(':checked:not(:disabled)').length,
    ).toEqual(2);

    allCheckbox.click();

    expect(
      document
        .getElementById('checkboxes')
        .querySelectorAll(':checked:not(:disabled)').length,
    ).toEqual(0);
  });

  it('should keep the select all checkbox in sync when individual checkboxes are all ticked', () => {
    const allCheckbox = document.getElementById('select-all');
    expect(allCheckbox.checked).toBe(false);

    [
      ...document.querySelectorAll(
        '[data-w-bulk-target="item"]:not([disabled])',
      ),
    ].forEach((itemCheckbox) => {
      itemCheckbox.click();
    });

    expect(allCheckbox.checked).toBe(true);

    [
      ...document.querySelectorAll(
        '[data-w-bulk-target="item"]:not([disabled])',
      ),
    ].forEach((itemCheckbox) => {
      itemCheckbox.click();
    });

    expect(allCheckbox.checked).toBe(false);
  });

  it('executes the correct action when the Clear all button is clicked', () => {
    const allCheckbox = document.getElementById('select-all');
    const clearAllButton = document.getElementById('clear');
    expect(allCheckbox.checked).toBe(false);

    [
      ...document.querySelectorAll(
        '[data-w-bulk-target="item"]:not([disabled])',
      ),
    ].forEach((itemCheckbox) => {
      itemCheckbox.click();
    });

    expect(allCheckbox.checked).toBe(true);

    clearAllButton.click();

    expect(
      document
        .getElementById('checkboxes')
        .querySelectorAll(':checked:not(:disabled)').length,
    ).toEqual(0);
    expect(allCheckbox.checked).toBe(false);
  });

  it('executes the correct action when the Set all button is clicked', () => {
    const allCheckbox = document.getElementById('select-all');
    const setAllButton = document.getElementById('set');

    expect(allCheckbox.checked).toBe(false);

    const checkboxes = document.querySelectorAll(
      '[data-w-bulk-target="item"]:not([disabled])',
    );

    expect(checkboxes.length).toEqual(2);

    setAllButton.click();

    expect(
      document
        .getElementById('checkboxes')
        .querySelectorAll(':checked:not(:disabled)').length,
    ).toEqual(2);

    expect(allCheckbox.checked).toBe(true);

    checkboxes.forEach((itemCheckbox) => {
      expect(itemCheckbox.checked).toBe(true);
    });
  });
});
