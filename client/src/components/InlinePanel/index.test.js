import $ from 'jquery';

import { InlinePanel } from './index';

jest.useFakeTimers();

describe('InlinePanel', () => {
  const handleAddedEvent = jest.fn();
  const handleRemovedEvent = jest.fn();
  const handleReadyEvent = jest.fn();

  const onAdd = jest.fn();

  beforeAll(() => {
    $.fx.off = true;
    jest.resetAllMocks();

    document.body.innerHTML = `
  <form>
    <input name="person_cafe_relationship-TOTAL_FORMS" value="0" id="id_person_cafe_relationship-TOTAL_FORMS" type="hidden" />
    <input name="person_cafe_relationship-INITIAL_FORMS" value="0" id="id_person_cafe_relationship-INITIAL_FORMS" type="hidden" />
    <input name="person_cafe_relationship-MIN_NUM_FORMS" value="1" id="id_person_cafe_relationship-MIN_NUM_FORMS" type="hidden" />
    <input name="person_cafe_relationship-MAX_NUM_FORMS" value="5" id="id_person_cafe_relationship-MAX_NUM_FORMS" type="hidden" />
    <div id="id_person_cafe_relationship-FORMS"></div>
    <template id="id_person_cafe_relationship-EMPTY_FORM_TEMPLATE">
      <div id="inline_child_person_cafe_relationship-__prefix__" data-child-form-mock>
        <p>Form for inline child</div>
        <button type="button" id="id_person_cafe_relationship-__prefix__-DELETE-button">Delete</button>
        <input type="hidden" name="id_person_cafe_relationship-__prefix__-DELETE" id="id_person_cafe_relationship-__prefix__-DELETE">
      </div>
    </template>
    <button type="button" id="id_person_cafe_relationship-ADD">Add item</button>
  </form>`;

    document.addEventListener('w-formset:added', handleAddedEvent);
    document.addEventListener('w-formset:ready', handleReadyEvent);
    document.addEventListener('w-formset:removed', handleRemovedEvent);
  });

  it('tests inline panel `w-formset:ready` event', () => {
    expect(handleReadyEvent).not.toHaveBeenCalled();

    const options = {
      emptyChildFormPrefix: 'person_cafe_relationship-__prefix__',
      formsetPrefix: 'id_person_cafe_relationship',
      onAdd,
    };

    new InlinePanel(options);

    jest.runAllTimers();

    expect(handleReadyEvent).toHaveBeenCalled();
  });

  it('should allow inserting a new form and also dispatches `w-formset:added` event on calling onAdd function', () => {
    expect(handleAddedEvent).not.toHaveBeenCalled();
    expect(onAdd).not.toHaveBeenCalled();
    expect(document.querySelectorAll('[data-child-form-mock]')).toHaveLength(0);

    // click the 'add' button
    document.getElementById('id_person_cafe_relationship-ADD').click();

    expect(document.querySelectorAll('[data-child-form-mock]')).toHaveLength(1);
    expect(onAdd).toHaveBeenCalled();

    document.getElementById('id_person_cafe_relationship-ADD').click();
    expect(onAdd).toHaveBeenCalledTimes(2);
    expect(document.querySelectorAll('[data-child-form-mock]')).toHaveLength(2);

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
    expect(document.querySelectorAll('[data-child-form-mock]')).toHaveLength(2);
    expect(
      document.querySelectorAll('.deleted[data-child-form-mock]'),
    ).toHaveLength(0);

    // click the 'delete' button
    document
      .getElementById('id_person_cafe_relationship-0-DELETE-button')
      .click();

    expect(document.querySelectorAll('[data-child-form-mock]')).toHaveLength(2);
    expect(
      document.querySelectorAll('.deleted[data-child-form-mock]'),
    ).toHaveLength(1);

    expect(handleRemovedEvent).toHaveBeenCalledTimes(1);
  });
});
