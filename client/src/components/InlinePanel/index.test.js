import $ from 'jquery';

import { InlinePanel } from './index';

jest.useFakeTimers();

describe('InlinePanel', () => {
  const handleAddedEvent = jest.fn();
  const handleRemovedEvent = jest.fn();
  const handleReadyEvent = jest.fn();

  const onAdd = jest.fn();
  let panel;

  beforeAll(() => {
    $.fx.off = true;
    jest.resetAllMocks();

    const prefix = 'person_cafe_relationship';
    const childPrefix = `${prefix}-__prefix__`;
    document.body.innerHTML = `
  <form>
    <input name="${prefix}-TOTAL_FORMS" value="0" id="id_${prefix}-TOTAL_FORMS" type="hidden" />
    <input name="${prefix}-INITIAL_FORMS" value="0" id="id_${prefix}-INITIAL_FORMS" type="hidden" />
    <input name="${prefix}-MIN_NUM_FORMS" value="1" id="id_${prefix}-MIN_NUM_FORMS" type="hidden" />
    <input name="${prefix}-MAX_NUM_FORMS" value="5" id="id_${prefix}-MAX_NUM_FORMS" type="hidden" />
    <div id="id_${prefix}-FORMS"></div>
    <template id="id_${prefix}-EMPTY_FORM_TEMPLATE">
      <div id="inline_child_${childPrefix}" data-inline-panel-child>
        <p>Form for inline child</p>
        <button type="button" data-inline-panel-child-move-up>Move up</button>
        <button type="button" data-inline-panel-child-move-down>Move down</button>
        <button type="button" data-inline-panel-child-drag>Drag</button>
        <button type="button" id="id_${childPrefix}-DELETE-button">Delete</button>
        <input type="hidden" name="${childPrefix}-ORDER" id="id_${childPrefix}-ORDER">
        <input type="hidden" name="${childPrefix}-DELETE" id="id_${childPrefix}-DELETE">
      </div>
    </template>
    <button type="button" id="id_${prefix}-ADD">Add item</button>
  </form>`;

    document.addEventListener('w-formset:added', handleAddedEvent);
    document.addEventListener('w-formset:ready', handleReadyEvent);
    document.addEventListener('w-formset:removed', handleRemovedEvent);

    expect(handleReadyEvent).not.toHaveBeenCalled();

    const options = {
      emptyChildFormPrefix: 'person_cafe_relationship-__prefix__',
      formsetPrefix: 'id_person_cafe_relationship',
      onAdd,
      canOrder: true,
    };

    panel = new InlinePanel(options);

    jest.runAllTimers();
  });

  it('tests inline panel `w-formset:ready` event', () => {
    expect(handleReadyEvent).toHaveBeenCalled();
  });

  it('should allow inserting a new form and also dispatches `w-formset:added` event on calling onAdd function', () => {
    expect(handleAddedEvent).not.toHaveBeenCalled();
    expect(onAdd).not.toHaveBeenCalled();
    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      0,
    );

    // click the 'add' button
    document.getElementById('id_person_cafe_relationship-ADD').click();

    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      1,
    );
    expect(onAdd).toHaveBeenCalled();

    document.getElementById('id_person_cafe_relationship-ADD').click();
    expect(onAdd).toHaveBeenCalledTimes(2);
    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      2,
    );

    // check events were dispatched
    expect(handleAddedEvent).toHaveBeenCalledTimes(2);
    const [event] = handleAddedEvent.mock.calls[0];

    expect(event.bubbles).toEqual(true);
    expect(event.detail).toMatchObject({
      formIndex: 0,
      formsetPrefix: 'id_person_cafe_relationship',
      emptyChildFormPrefix: 'person_cafe_relationship-__prefix__',
    });
  });

  it('should allow removing a form', async () => {
    expect(handleRemovedEvent).not.toHaveBeenCalled();
    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      2,
    );
    expect(
      document.querySelectorAll('.deleted[data-inline-panel-child]'),
    ).toHaveLength(0);

    // click the 'delete' button
    document
      .getElementById('id_person_cafe_relationship-0-DELETE-button')
      .click();

    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      2,
    );
    expect(
      document.querySelectorAll('.deleted[data-inline-panel-child]'),
    ).toHaveLength(1);

    expect(handleRemovedEvent).toHaveBeenCalledTimes(1);
  });

  it('updates order values after drag-and-drop', () => {
    const addBtn = document.getElementById('id_person_cafe_relationship-ADD');
    addBtn.click();
    addBtn.click();

    // Simulate drag-and-drop by manually moving an element.
    const forms = document.querySelectorAll(
      '[data-inline-panel-child]:not(.deleted)',
    );
    forms[0].parentElement.insertBefore(forms[0], forms[2]);
    panel.handleDragEnd({ oldIndex: 0, newIndex: 2 });

    expect(
      Array.from(
        document.querySelectorAll(
          '[data-inline-panel-child]:not(.deleted) [name$="-ORDER"]',
        ),
      ).map((field) => [field.name, field.value]),
    ).toEqual([
      ['person_cafe_relationship-2-ORDER', '1'],
      ['person_cafe_relationship-1-ORDER', '2'],
      ['person_cafe_relationship-3-ORDER', '3'],
    ]);
  });
});

describe('InlinePanel with initial forms', () => {
  const prefix = 'person_cafe_relationship';
  const childPrefix = `${prefix}-__prefix__`;

  /**
   * Render the markup for a single child form. A nested InlinePanel's child
   * (with its own move and count elements) can be included to ensure that only
   * the outer panel's controls are affected.
   */
  const renderChild = (
    childFormPrefix,
    { order = '', deleted = '', nested = false } = {},
  ) => `
    <div id="inline_child_${childFormPrefix}" data-inline-panel-child>
      <h2>Item<span data-inline-panel-child-count></span></h2>
      <button type="button" data-inline-panel-child-move-up>Move up</button>
      <button type="button" data-inline-panel-child-move-down>Move down</button>
      <button type="button" id="id_${childFormPrefix}-DELETE-button">Delete</button>
      <input type="hidden" name="${childFormPrefix}-ORDER" id="id_${childFormPrefix}-ORDER" value="${order}">
      <input type="hidden" name="${childFormPrefix}-DELETE" id="id_${childFormPrefix}-DELETE" value="${deleted}">
      <p class="error-message">This field is required.</p>
      ${
        nested
          ? `<div data-inline-panel-child>
              <h3>Nested item<span data-inline-panel-child-count></span></h3>
              <button type="button" data-inline-panel-child-move-up>Nested move up</button>
              <button type="button" data-inline-panel-child-move-down>Nested move down</button>
            </div>`
          : ''
      }
    </div>`;

  const setup = ({ children = [], opts = {} } = {}) => {
    document.body.innerHTML = `
    <form>
      <input name="${prefix}-TOTAL_FORMS" value="${children.length}" id="id_${prefix}-TOTAL_FORMS" type="hidden" />
      <input name="${prefix}-INITIAL_FORMS" value="${children.length}" id="id_${prefix}-INITIAL_FORMS" type="hidden" />
      <input name="${prefix}-MIN_NUM_FORMS" value="0" id="id_${prefix}-MIN_NUM_FORMS" type="hidden" />
      <input name="${prefix}-MAX_NUM_FORMS" value="1000" id="id_${prefix}-MAX_NUM_FORMS" type="hidden" />
      <div id="id_${prefix}-FORMS">${children
        .map((childOpts, i) => renderChild(`${prefix}-${i}`, childOpts))
        .join('')}</div>
      <template id="id_${prefix}-EMPTY_FORM_TEMPLATE">${renderChild(
        childPrefix,
      )}</template>
      <button type="button" id="id_${prefix}-ADD">Add item</button>
    </form>`;

    const panel = new InlinePanel({
      emptyChildFormPrefix: childPrefix,
      formsetPrefix: `id_${prefix}`,
      canOrder: true,
      ...opts,
    });
    jest.runAllTimers();
    return panel;
  };

  const getChild = (index) =>
    document.getElementById(`inline_child_${prefix}-${index}`);

  const getOrderValues = () =>
    Array.from(
      document.querySelectorAll(
        `#id_${prefix}-FORMS > [data-inline-panel-child]:not(.deleted) [name$="-ORDER"]`,
      ),
    ).map((field) => [field.name, field.value]);

  const getMoveButtonStates = () =>
    Array.from(
      document.querySelectorAll(
        `#id_${prefix}-FORMS > [data-inline-panel-child]:not(.deleted)`,
      ),
    ).map((child) => [
      child.querySelector('[data-inline-panel-child-move-up]').disabled,
      child.querySelector('[data-inline-panel-child-move-down]').disabled,
    ]);

  beforeEach(() => {
    $.fx.off = true;
  });

  afterEach(() => {
    jest.runAllTimers();
  });

  it('should set the child count labels and move button states on load', () => {
    setup({
      children: [{ order: '1' }, { order: '2' }, { order: '3' }],
    });

    expect(
      Array.from(
        document.querySelectorAll(
          `#id_${prefix}-FORMS > [data-inline-panel-child] [data-inline-panel-child-count]`,
        ),
      ).map((count) => count.textContent),
    ).toEqual([' 1', ' 2', ' 3']);

    expect(getMoveButtonStates()).toEqual([
      [true, false],
      [false, false],
      [false, true],
    ]);
  });

  it('should hide children marked as deleted on load and remove their error messages', () => {
    setup({
      children: [{ order: '1' }, { order: '2', deleted: '1' }, { order: '3' }],
    });

    const deletedChild = getChild(1);
    expect(deletedChild.classList.contains('deleted')).toBe(true);
    expect(deletedChild.style.display).toEqual('none');
    expect(deletedChild.querySelector('.error-message')).toBeNull();

    // Other children keep their error messages
    expect(getChild(0).querySelector('.error-message')).not.toBeNull();

    // Deleted children are ignored when numbering and setting button states
    expect(
      getChild(0).querySelector('[data-inline-panel-child-count]').textContent,
    ).toEqual(' 1');
    expect(
      getChild(2).querySelector('[data-inline-panel-child-count]').textContent,
    ).toEqual(' 2');
    expect(getMoveButtonStates()).toEqual([
      [true, false],
      [false, true],
    ]);
  });

  it('should set the DELETE field when removing a child and update the remaining children', () => {
    const handleChange = jest.fn();
    document.addEventListener('change', handleChange);

    setup({
      children: [{ order: '1' }, { order: '2' }, { order: '3' }],
    });

    document.getElementById(`id_${prefix}-0-DELETE-button`).click();

    expect(document.getElementById(`id_${prefix}-0-DELETE`).value).toEqual('1');
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange.mock.calls[0][0].target.id).toEqual(
      `id_${prefix}-0-DELETE`,
    );
    expect(
      getChild(1).querySelector('[data-inline-panel-child-count]').textContent,
    ).toEqual(' 1');
    expect(getMoveButtonStates()).toEqual([
      [true, false],
      [false, true],
    ]);

    document.removeEventListener('change', handleChange);
  });

  it('should swap a child with the previous one when moving up', () => {
    setup({
      children: [{ order: '1' }, { order: '2' }, { order: '3' }],
    });

    getChild(2).querySelector('[data-inline-panel-child-move-up]').click();

    expect(getOrderValues()).toEqual([
      [`${prefix}-0-ORDER`, '1'],
      [`${prefix}-2-ORDER`, '2'],
      [`${prefix}-1-ORDER`, '3'],
    ]);
    expect(getMoveButtonStates()).toEqual([
      [true, false],
      [false, false],
      [false, true],
    ]);
  });

  it('should swap a child with the next one when moving down', () => {
    setup({
      children: [{ order: '1' }, { order: '2' }, { order: '3' }],
    });

    getChild(0).querySelector('[data-inline-panel-child-move-down]').click();

    expect(getOrderValues()).toEqual([
      [`${prefix}-1-ORDER`, '1'],
      [`${prefix}-0-ORDER`, '2'],
      [`${prefix}-2-ORDER`, '3'],
    ]);
  });

  it('should skip deleted children when moving', () => {
    setup({
      children: [{ order: '1' }, { order: '2', deleted: '1' }, { order: '3' }],
    });

    getChild(2).querySelector('[data-inline-panel-child-move-up]').click();

    expect(getOrderValues()).toEqual([
      [`${prefix}-2-ORDER`, '1'],
      [`${prefix}-0-ORDER`, '3'],
    ]);
    expect(
      Array.from(
        document.querySelectorAll(
          `#id_${prefix}-FORMS > [data-inline-panel-child]`,
        ),
      ).map((child) => child.id),
    ).toEqual([
      `inline_child_${prefix}-2`,
      `inline_child_${prefix}-0`,
      `inline_child_${prefix}-1`,
    ]);
  });

  it('should not change anything when moving the first child up', () => {
    setup({
      children: [{ order: '1' }, { order: '2' }],
    });

    getChild(0).querySelector('[data-inline-panel-child-move-up]').click();

    expect(getOrderValues()).toEqual([
      [`${prefix}-0-ORDER`, '1'],
      [`${prefix}-1-ORDER`, '2'],
    ]);
  });

  it('should only update the outer panel controls when children contain a nested InlinePanel', () => {
    setup({
      children: [
        { order: '1', nested: true },
        { order: '2', nested: true },
      ],
    });

    // Only the first count element within each child is updated
    expect(
      Array.from(
        document.querySelectorAll(
          '[data-inline-panel-child] [data-inline-panel-child] [data-inline-panel-child-count]',
        ),
      ).map((count) => count.textContent),
    ).toEqual(['', '']);

    // Nested move buttons are left untouched
    const nestedMoveButtons = document.querySelectorAll(
      '[data-inline-panel-child] [data-inline-panel-child] button',
    );
    expect(
      Array.from(nestedMoveButtons).map((button) => button.disabled),
    ).toEqual([false, false, false, false]);

    // Clicking the outer move down button moves the outer child
    getChild(0).querySelector('[data-inline-panel-child-move-down]').click();
    expect(getOrderValues()).toEqual([
      [`${prefix}-1-ORDER`, '1'],
      [`${prefix}-0-ORDER`, '2'],
    ]);
  });

  it('should set the ORDER value for a newly added child', () => {
    setup({
      children: [{ order: '1' }, { order: '2' }],
    });

    document.getElementById(`id_${prefix}-ADD`).click();

    expect(document.getElementById(`id_${prefix}-TOTAL_FORMS`).value).toEqual(
      '3',
    );
    expect(getOrderValues()).toEqual([
      [`${prefix}-0-ORDER`, '1'],
      [`${prefix}-1-ORDER`, '2'],
      [`${prefix}-2-ORDER`, '3'],
    ]);
    expect(getMoveButtonStates()).toEqual([
      [true, false],
      [false, false],
      [false, true],
    ]);
  });

  it('should not run the onAdd and onInit callbacks when runCallbacks is false', () => {
    const onAdd = jest.fn();
    const onInit = jest.fn();
    const panel = setup({ opts: { onAdd, onInit } });

    panel.addForm({ runCallbacks: false });
    expect(onAdd).not.toHaveBeenCalled();
    expect(onInit).not.toHaveBeenCalled();

    panel.addForm();
    expect(onAdd).toHaveBeenCalledWith(1);
    expect(onInit).toHaveBeenCalledWith(1);
  });

  it('should disable the add button once the maximum number of forms is reached', () => {
    setup({
      children: [{ order: '1' }],
      opts: { maxForms: 2 },
    });

    const addButton = document.getElementById(`id_${prefix}-ADD`);
    expect(addButton.disabled).toBe(false);

    addButton.click();
    expect(addButton.disabled).toBe(true);

    // Removing a child allows adding again
    document.getElementById(`id_${prefix}-0-DELETE-button`).click();
    expect(addButton.disabled).toBe(false);
  });
});
