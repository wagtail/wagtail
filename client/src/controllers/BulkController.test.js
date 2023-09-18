import { Application } from '@hotwired/stimulus';
import { BulkController } from './BulkController';

describe('BulkController', () => {
  beforeEach(() => {
    document.body.innerHTML = `
    <div id="bulk-container" data-controller="w-bulk">
      <input id="select-all" type="checkbox" data-w-bulk-target="all" data-action="w-bulk#toggleAll">
      <div id="checkboxes">
        <input type="checkbox" data-w-bulk-target="item" disabled data-action="w-bulk#toggle">
        <input type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
        <input type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
      </div>
      <button id="clear" data-action="w-bulk#toggleAll" data-w-bulk-force-param="false">Clear all</button>
      <button id="set" data-action="w-bulk#toggleAll" data-w-bulk-force-param="true">Select all</button>
    </div>`;
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

  it('should allow for action targets to have classes toggled when any checkboxes are clicked', async () => {
    const container = document.getElementById('bulk-container');

    // create innerActions container that will be conditionally hidden with test classes
    container.setAttribute(
      'data-w-bulk-action-inactive-class',
      'hidden w-invisible',
    );
    const innerActions = document.createElement('div');
    innerActions.id = 'inner-actions';
    innerActions.className = 'keep-me hidden w-invisible';
    innerActions.setAttribute('data-w-bulk-target', 'action');
    container.prepend(innerActions);

    const innerActionsElement = document.getElementById('inner-actions');

    expect(
      document
        .getElementById('checkboxes')
        .querySelectorAll(':checked:not(:disabled)').length,
    ).toEqual(0);

    expect(innerActionsElement.className).toEqual('keep-me hidden w-invisible');

    const firstCheckbox = document
      .getElementById('checkboxes')
      .querySelector("[type='checkbox']:not([disabled])");

    firstCheckbox.click();

    expect(innerActionsElement.className).toEqual('keep-me');

    firstCheckbox.click();

    expect(innerActionsElement.className).toEqual('keep-me hidden w-invisible');
  });
});
