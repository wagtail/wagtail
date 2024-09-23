import { Application } from '@hotwired/stimulus';
import { BulkController } from './BulkController';

describe('BulkController', () => {
  let application;
  let handleError;

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

    application = Application.start();
    application.register('w-bulk', BulkController);
    handleError = jest.fn();
    application.handleError = handleError;
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

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

  describe('support for groups of checkboxes being used', () => {
    const html = `
    <table id="table" data-controller="w-bulk" data-action="custom:event->w-bulk#toggleAll">
      <caption>
        Misc items
        <input id="misc-any" data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="add change delete" type="checkbox"/>
        <input id="misc-add-change" data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="add change" type="checkbox"/>
        <input id="misc-change-delete" data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="change delete" type="checkbox"/>
        <input id="misc-add-change-delete" data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="add change delete" type="checkbox"/>
      </caption>
      <thead>
        <tr><th>Name</th><th>Add</th><th>Change</th><th>Delete</th></tr>
      </thead>
      <tbody>
      ${[...Array(5).keys()]
        .map(
          (i) => `
        <tr id="row-${i}">
          <td>Item ${i + 1}</td>
          <td><input id="row-${i}-add" data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="add" type="checkbox"/></td>
          <td><input id="row-${i}-change" data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="change" type="checkbox"/></td>
          <td><input id="row-${i}-delete" data-action="w-bulk#toggle" data-w-bulk-target="item" data-w-bulk-group-param="delete" type="checkbox"/></td>
        </tr>`,
        )
        .join('\n')}
      </tbody>
      <tfoot>
        <th scope="row">
          Check all (Add & Change)
          <input id="select-all" data-action="w-bulk#toggleAll" data-w-bulk-target="all" type="checkbox"/>
          <input id="select-all-add-change" data-action="w-bulk#toggleAll" data-w-bulk-target="all" data-w-bulk-group-param="add change" type="checkbox"/>
        </th>
        <td>
          Check all (Add)
          <input id="select-all-add" data-action="w-bulk#toggleAll" data-w-bulk-target="all" data-w-bulk-group-param="add" type="checkbox"/>
        </td>
        <td>
          Check all (Change)
          <input id="select-all-change" data-action="w-bulk#toggleAll" data-w-bulk-target="all" data-w-bulk-group-param="change" type="checkbox"/>
        </td>
        <td>
          Check all (Delete)
          <input id="select-all-delete" data-action="w-bulk#toggleAll" data-w-bulk-target="all" data-w-bulk-group-param="delete" type="checkbox"/>
        </td>
       </tfoot>
    </table>
    `;

    it('should allow for the toggleAll method to be used to select all, irrespective of groupings', async () => {
      const totalCheckboxes = 24;

      await setup(html);

      const allCheckbox = document.getElementById('select-all');
      expect(allCheckbox.checked).toBe(false);
      expect(document.querySelectorAll('[type="checkbox"')).toHaveLength(
        totalCheckboxes,
      );
      expect(document.querySelectorAll(':checked')).toHaveLength(0);

      allCheckbox.click();

      expect(allCheckbox.checked).toBe(true);
      expect(document.querySelectorAll(':checked')).toHaveLength(
        totalCheckboxes,
      );

      allCheckbox.click();
      expect(document.querySelectorAll(':checked')).toHaveLength(0);
    });

    it('should allow for the toggleAll method to be used for single group toggling', async () => {
      await setup(html);

      expect(document.querySelectorAll(':checked')).toHaveLength(0);

      document.getElementById('select-all-delete').click();

      const checked = document.querySelectorAll(':checked');

      expect(checked).toHaveLength(9);

      expect(checked).toEqual(
        document.querySelectorAll('[data-w-bulk-group-param~="delete"]'),
      );

      const otherCheckbox = document.getElementById('row-3-add');

      otherCheckbox.click();

      expect(document.querySelectorAll(':checked')).toHaveLength(10);

      document.getElementById('select-all-delete').click();

      expect(document.querySelectorAll(':checked')).toHaveLength(1);
      expect(otherCheckbox.checked).toEqual(true);
    });

    it('should allow for the toggleAll method to be used for multi group toggling', async () => {
      await setup(html);

      expect(document.querySelectorAll(':checked')).toHaveLength(0);

      document.getElementById('select-all-add-change').click();

      const checked = document.querySelectorAll(':checked');
      expect(checked).toHaveLength(17);
      expect([...checked].map(({ id }) => id)).toEqual(
        expect.arrayContaining([
          'misc-any',
          'misc-add-change',
          'misc-change-delete',
          'misc-add-change-delete',
          'row-0-add',
          'row-0-change',
          // ... others not needing explicit call out
        ]),
      );

      // specific group select all checkboxes should now be checked automatically
      expect(document.getElementById('select-all-add').checked).toEqual(true);
      expect(document.getElementById('select-all-change').checked).toEqual(
        true,
      );
    });

    it('should support shift+click within the groups', async () => {
      await setup(html);

      expect(document.querySelectorAll(':checked')).toHaveLength(0);

      document.getElementById('row-0-change').click();

      await shiftClick(document.getElementById('row-2-change'));

      // only checkboxes in
      expect(document.getElementById('row-1-change').checked).toEqual(true);
      expect(document.querySelectorAll(':checked')).toHaveLength(3);

      // now shift again to the last checkbox
      await shiftClick(document.getElementById('row-4-change'));
      expect(document.getElementById('row-3-change').checked).toEqual(true);
      expect(document.querySelectorAll(':checked')).toHaveLength(5);
    });

    it('should not throw an error when shift+clicking across groups', async () => {
      await setup(html);
      expect(document.querySelectorAll(':checked')).toHaveLength(0);
      document.getElementById('row-0-add').click();

      // Same row, different group
      await shiftClick(document.getElementById('row-0-change'));

      // Should not throw an error, and only select the two checkboxes
      expect(application.handleError).not.toHaveBeenCalled();
      expect(document.getElementById('row-0-add').checked).toEqual(true);
      expect(document.getElementById('row-0-change').checked).toEqual(true);
      expect(document.querySelectorAll(':checked')).toHaveLength(2);

      document.getElementById('row-1-change').click();

      // Different row, different group
      await shiftClick(document.getElementById('row-3-add'));

      // Should not throw an error, and only select the two checkboxes
      // in addition to the two already selected
      expect(application.handleError).not.toHaveBeenCalled();
      expect(document.getElementById('row-1-change').checked).toEqual(true);
      expect(document.getElementById('row-3-add').checked).toEqual(true);
      expect(document.getElementById('row-0-add').checked).toEqual(true);
      expect(document.getElementById('row-0-change').checked).toEqual(true);
      expect(document.querySelectorAll(':checked')).toHaveLength(4);
    });

    it('should support the group being passed in via a CustomEvent', async () => {
      await setup(html);

      const table = document.getElementById('table');
      expect(document.querySelectorAll(':checked')).toHaveLength(0);

      table.dispatchEvent(
        new CustomEvent('custom:event', { detail: { group: 'delete' } }),
      );

      await Promise.resolve();

      const checked = document.querySelectorAll(':checked');

      expect(checked).toHaveLength(9);
      expect([...checked].map(({ id }) => id)).toEqual([
        'misc-any',
        'misc-change-delete',
        'misc-add-change-delete',
        'row-0-delete',
        'row-1-delete',
        'row-2-delete',
        'row-3-delete',
        'row-4-delete',
        'select-all-delete',
      ]);

      // now check one of the non-delete checkboxes
      document.getElementById('row-0-add').click();
      expect(document.querySelectorAll(':checked')).toHaveLength(10);

      // use force to toggle only the delete checkboxes off
      table.dispatchEvent(
        new CustomEvent('custom:event', {
          detail: { group: 'delete', force: false },
        }),
      );

      expect(document.querySelectorAll(':checked')).toHaveLength(1);

      // run a second time to confirm there should be no difference due to force
      table.dispatchEvent(
        new CustomEvent('custom:event', {
          detail: { group: 'delete', force: false },
        }),
      );

      expect(document.querySelectorAll(':checked')).toHaveLength(1);
    });
  });
});
