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
