import { Application } from '@hotwired/stimulus';
import { BulkController } from './BulkController';

describe('BulkController', () => {
  const setup = async (
    html = `
    <div id="bulk-container" data-controller="w-bulk" data-action="custom:event@document->w-bulk#toggleAll">
      <input id="select-all" type="checkbox" data-w-bulk-target="all" data-action="w-bulk#toggleAll">
      <div id="checkboxes">
        <input type="checkbox" data-w-bulk-target="item" disabled data-action="w-bulk#toggle">
        <input type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
        <input type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
      </div>
      <button id="clear" data-action="w-bulk#toggleAll" data-w-bulk-force-param="false">Clear all</button>
      <button id="set" data-action="w-bulk#toggleAll" data-w-bulk-force-param="true">Select all</button>
    </div>`,
  ) => {
    document.body.innerHTML = `<main>${html}</main>`;

    const application = Application.start();
    application.register('w-bulk', BulkController);
  };

  it('selects all checkboxes when the select all checkbox is clicked', async () => {
    await setup();

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

  it('should keep the select all checkbox in sync when individual checkboxes are all ticked', async () => {
    await setup();

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

  it('executes the correct action when the Clear all button is clicked', async () => {
    await setup();

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

  it('executes the correct action when the Set all button is clicked', async () => {
    await setup();

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

  it('should support using another method (e.g. CustomEvent) to toggle all', async () => {
    await setup();

    const allCheckbox = document.getElementById('select-all');
    expect(allCheckbox.checked).toBe(false);

    document.dispatchEvent(new CustomEvent('custom:event'));

    expect(allCheckbox.checked).toBe(true);
    expect(document.querySelectorAll(':checked')).toHaveLength(3);

    // calling again, should switch the toggles back

    document.dispatchEvent(new CustomEvent('custom:event'));

    expect(allCheckbox.checked).toBe(false);
    expect(document.querySelectorAll(':checked')).toHaveLength(0);
  });

  it('should support a force value in a CustomEvent to override the select all checkbox', async () => {
    await setup();

    const allCheckbox = document.getElementById('select-all');
    expect(allCheckbox.checked).toBe(false);

    document.dispatchEvent(
      new CustomEvent('custom:event', { detail: { force: true } }),
    );

    expect(allCheckbox.checked).toBe(true);
    expect(document.querySelectorAll(':checked')).toHaveLength(3);

    // calling again, should not change the state of the checkboxes
    document.dispatchEvent(
      new CustomEvent('custom:event', { detail: { force: true } }),
    );

    expect(allCheckbox.checked).toBe(true);
    expect(document.querySelectorAll(':checked')).toHaveLength(3);
  });

  it('should allow for action targets to have classes toggled when any checkboxes are clicked', async () => {
    await setup();

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

  it('should support shift+click to select a range of checkboxes', async () => {
    await setup(`
    <div id="bulk-container-multi" data-controller="w-bulk">
      <input id="select-all-multi" type="checkbox" data-w-bulk-target="all" data-action="w-bulk#toggleAll">
      <div id="checkboxes">
        <input id="c0" type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
        <input id="c1" type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
        <input id="cx" type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle" disabled>
        <input id="c2" type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
        <input id="c3" type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
        <input id="c4" type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
        <input id="c5" type="checkbox" data-w-bulk-target="item" data-action="w-bulk#toggle">
      </div>
    </div>`);

    const getClickedIds = () =>
      Array.from(document.querySelectorAll(':checked')).map(({ id }) => id);

    const shiftClick = async (element) => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', {
          key: 'Shift',
          shiftKey: true,
        }),
      );
      element.click();
      document.dispatchEvent(
        new KeyboardEvent('keyup', {
          key: 'Shift',
          shiftKey: true,
        }),
      );
      await Promise.resolve();
    };

    // initial shift usage should have no impact
    await shiftClick(document.getElementById('c0'));
    expect(getClickedIds()).toHaveLength(1);

    // shift click should select all checkboxes between the first and last clicked
    await shiftClick(document.getElementById('c2'));
    expect(getClickedIds()).toEqual(['c0', 'c1', 'c2']);

    await shiftClick(document.getElementById('c5'));
    expect(getClickedIds()).toEqual([
      'select-all-multi',
      'c0',
      'c1',
      'c2',
      'c3',
      'c4',
      'c5',
    ]);

    // it should allow reverse clicks
    document.getElementById('c4').click(); // un-click
    expect(getClickedIds()).toEqual(['c0', 'c1', 'c2', 'c3', 'c5']);

    // now shift click in reverse, un-clicking those between the last (4) and the new click (1)
    await shiftClick(document.getElementById('c1'));
    expect(getClickedIds()).toEqual(['c0', 'c5']);

    // reset the clicks, then using shift click should do nothing
    document.getElementById('select-all-multi').click();
    document.getElementById('select-all-multi').click();
    expect(getClickedIds()).toHaveLength(0);

    await shiftClick(document.getElementById('c4'));
    expect(getClickedIds()).toEqual(['c4']);

    // finally, do a shift click to the first checkbox, check the select all works after a final click
    await shiftClick(document.getElementById('c0'));
    expect(getClickedIds()).toEqual(['c0', 'c1', 'c2', 'c3', 'c4']);

    document.getElementById('c5').click();

    expect(getClickedIds()).toEqual([
      'select-all-multi',
      'c0',
      'c1',
      'c2',
      'c3',
      'c4',
      'c5',
    ]);

    // now ensure that it still works if some element gets changed (not disabled)
    document.getElementById('cx').removeAttribute('disabled');
    document.getElementById('select-all-multi').click();
    expect(getClickedIds()).toHaveLength(0);

    await Promise.resolve();

    document.getElementById('c3').click(); // click

    await shiftClick(document.getElementById('c1'));

    // it should include the previously disabled element, tracking against the DOM, not indexes
    expect(getClickedIds()).toEqual(['c1', 'cx', 'c2', 'c3']);
  });
});
