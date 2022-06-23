/* global buildExpandingFormset */
import $ from 'jquery';

window.$ = $;

import './expanding-formset';

describe('buildExpandingFormset', () => {
  it('exposes module as global', () => {
    expect(window.buildExpandingFormset).toBeDefined();
  });

  it('should add an expanded item if the add button is not disabled', () => {
    const prefix = 'id_form_fields';
    document.body.innerHTML = `
    <div class="object" id="content">
      <input type="hidden" name="form_fields-TOTAL_FORMS" value="2" id="${prefix}-TOTAL_FORMS">
      <ul id="${prefix}-FORMS">
        ${[0, 1].map(
          (id) => `
        <li id="inline_child_form_fields-${id}" data-inline-panel-child data-contentpath-disabled>
          <input type="text" name="form_fields-${id}-label" value="Subject" id="id_form_fields-${id}-label">
          <input type="hidden" name="form_fields-${id}-id" value="${
            id + 1
          }" id="id_form_fields-${id}-id">
          <input type="hidden" name="form_fields-${id}-DELETE" id="id_form_fields-${id}-DELETE">
        </li>
        `,
        )}
      </ul>
      <button class="button" id="${prefix}-ADD" type="button">
        Add form fields
      </button>
      <script type="text/django-form-template" id="${prefix}-EMPTY_FORM_TEMPLATE">
        <li id="inline_child_form_fields-__prefix__" data-inline-panel-child data-contentpath-disabled>
          <input type="text" name="form_fields-__prefix__-label" id="id_form_fields-__prefix__-label">
          <input type="hidden" name="form_fields-__prefix__-id" id="id_form_fields-__prefix__-id">
          <input type="hidden" name="form_fields-__prefix__-DELETE" id="id_form_fields-__prefix__-DELETE">
        </li>
      </script>
    </div>`;

    const onAdd = jest.fn();
    const onInit = jest.fn();

    expect(document.getElementById(`${prefix}-TOTAL_FORMS`).value).toEqual('2');
    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      2,
    );
    expect(onAdd).not.toHaveBeenCalled();
    expect(onInit).not.toHaveBeenCalled();

    // initialise expanding formset
    buildExpandingFormset(prefix, { onInit, onAdd });

    // check that init calls only were made for existing items
    expect(onAdd).not.toHaveBeenCalled();
    expect(onInit).toHaveBeenCalledTimes(2);
    expect(onInit).toHaveBeenNthCalledWith(1, 0); // zero indexed
    expect(onInit).toHaveBeenNthCalledWith(2, 1);

    // click the 'add' button
    document
      .getElementById(`${prefix}-ADD`)
      .dispatchEvent(new MouseEvent('click'));

    // check that template was generated and additional onInit / onAdd called
    expect(onAdd).toHaveBeenCalledWith(2); // zero indexed
    expect(onInit).toHaveBeenCalledTimes(3);
    expect(onInit).toHaveBeenLastCalledWith(2);
    expect(document.getElementById(`${prefix}-TOTAL_FORMS`).value).toEqual('3');
    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      3,
    );

    // check template was created into a new form item or malformed
    expect(
      document.getElementById('inline_child_form_fields-__prefix__'),
    ).toBeNull();
    const newFormHtml = document.getElementById(
      `inline_child_form_fields-${2}`,
    );
    expect(newFormHtml.querySelectorAll('[id*="__prefix__"]')).toHaveLength(0);
    expect(
      newFormHtml.querySelectorAll(`[id*="form_fields-${2}"]`),
    ).toHaveLength(3);

    expect(newFormHtml).toMatchSnapshot();
  });

  it('should not add an expanded item if the add button is disabled', () => {
    const prefix = 'id_form_fields';
    document.body.innerHTML = `
    <div class="object" id="content">
      <input type="hidden" name="form_fields-TOTAL_FORMS" value="2" id="${prefix}-TOTAL_FORMS">
      <ul id="${prefix}-FORMS">
        ${[0, 1].map(
          (id) => `
        <li id="inline_child_form_fields-${id}" data-inline-panel-child data-contentpath-disabled>
          <input type="text" name="form_fields-${id}-label" value="Subject" id="id_form_fields-${id}-label">
          <input type="hidden" name="form_fields-${id}-id" value="${
            id + 1
          }" id="id_form_fields-${id}-id">
          <input type="hidden" name="form_fields-${id}-DELETE" id="id_form_fields-${id}-DELETE">
        </li>
        `,
        )}
      </ul>
      <button class="button disabled" id="${prefix}-ADD" type="button">
        Add form fields (DISABLED)
      </button>
      <script type="text/django-form-template" id="${prefix}-EMPTY_FORM_TEMPLATE">
        <li id="inline_child_form_fields-__prefix__" data-inline-panel-child data-contentpath-disabled>
          <input type="text" name="form_fields-__prefix__-label" id="id_form_fields-__prefix__-label">
          <input type="hidden" name="form_fields-__prefix__-id" id="id_form_fields-__prefix__-id">
          <input type="hidden" name="form_fields-__prefix__-DELETE" id="id_form_fields-__prefix__-DELETE">
        </li>
      </script>
    </div>`;

    const onAdd = jest.fn();
    const onInit = jest.fn();

    expect(document.getElementById(`${prefix}-TOTAL_FORMS`).value).toEqual('2');
    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      2,
    );
    expect(onAdd).not.toHaveBeenCalled();
    expect(onInit).not.toHaveBeenCalled();

    // initialise expanding formset
    buildExpandingFormset(prefix, { onInit, onAdd });

    // check that init calls only were made for existing items
    expect(onInit).toHaveBeenCalledTimes(2);
    expect(onInit).toHaveBeenNthCalledWith(1, 0); // zero indexed
    expect(onInit).toHaveBeenNthCalledWith(2, 1);

    // click the 'add' button
    document
      .getElementById(`${prefix}-ADD`)
      .dispatchEvent(new MouseEvent('click'));

    // check that no template was generated and additional onInit / onAdd not called
    expect(onAdd).not.toHaveBeenCalled();
    expect(onInit).toHaveBeenCalledTimes(2);
    expect(document.getElementById(`${prefix}-TOTAL_FORMS`).value).toEqual('2');
    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      2,
    );

    // check template was not created into a new form item or malformed
    expect(
      document.getElementById('inline_child_form_fields-__prefix__'),
    ).toBeNull();
  });

  it('should replace the __prefix__ correctly for nested formset templates', () => {
    const prefix = 'id_venues';
    const nestedPrefix = 'events';

    const nestedTemplate = `
<script type="text/django-form-template" id="${prefix}-__prefix__-events-EMPTY_FORM_TEMPLATE">
  <ul class="controls">
    <li>
      <button type="button" class="button" id="${prefix}-__prefix__-${nestedPrefix}-__prefix__-DELETE-button">
        Delete
      </button>
    </li>
  </ul>
  <fieldset>
    <legend>Events</legend>
    <input type="text" name="venues-__prefix__-events-__prefix__-name" id="id_venues-__prefix__-events-__prefix__-name">
  </fieldset>
<-/script>
    `;

    document.body.innerHTML = `
    <div class="object" id="content">
      <input type="hidden" name="form_fields-TOTAL_FORMS" value="2" id="${prefix}-TOTAL_FORMS">
      <ul id="${prefix}-FORMS">
        ${[0, 1].map(
          (id) => `
        <li id="inline_child_form_fields-${id}" data-inline-panel-child data-contentpath-disabled>
          <input type="text" name="form_fields-${id}-label" value="Subject" id="id_form_fields-${id}-label">
          <input type="hidden" name="form_fields-${id}-id" value="${
            id + 1
          }" id="id_form_fields-${id}-id">
          <input type="hidden" name="form_fields-${id}-DELETE" id="id_form_fields-${id}-DELETE">
        </li>
        `,
        )}
      </ul>
      <button class="button" id="${prefix}-ADD" type="button">
        Add Venue
      </button>
      <script type="text/django-form-template" id="${prefix}-EMPTY_FORM_TEMPLATE">
        <li id="inline_child_form_fields-__prefix__" data-inline-panel-child data-contentpath-disabled>
          <input type="text" name="form_fields-__prefix__-label" id="id_form_fields-__prefix__-label">
          <input type="hidden" name="form_fields-__prefix__-id" id="id_form_fields-__prefix__-id">
          <input type="hidden" name="form_fields-__prefix__-DELETE" id="id_form_fields-__prefix__-DELETE">
        </li>
        ${nestedTemplate}
      </script>
    </div>`;

    const onAdd = jest.fn();
    const onInit = jest.fn();

    expect(document.getElementById(`${prefix}-TOTAL_FORMS`).value).toEqual('2');
    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      2,
    );
    expect(onAdd).not.toHaveBeenCalled();
    expect(onInit).not.toHaveBeenCalled();

    // initialise expanding formset
    buildExpandingFormset(prefix, { onInit, onAdd });

    // check that init calls only were made for existing items
    expect(onAdd).not.toHaveBeenCalled();
    expect(onInit).toHaveBeenCalledTimes(2);
    expect(onInit).toHaveBeenNthCalledWith(1, 0); // zero indexed
    expect(onInit).toHaveBeenNthCalledWith(2, 1);

    // click the 'add' button
    document
      .getElementById(`${prefix}-ADD`)
      .dispatchEvent(new MouseEvent('click'));

    // check that template was generated and additional onInit / onAdd called
    expect(onAdd).toHaveBeenCalledWith(2); // zero indexed
    expect(onInit).toHaveBeenCalledTimes(3);
    expect(onInit).toHaveBeenLastCalledWith(2);
    expect(document.getElementById(`${prefix}-TOTAL_FORMS`).value).toEqual('3');
    expect(document.querySelectorAll('[data-inline-panel-child]')).toHaveLength(
      3,
    );

    // check the nested template was created with the correct prefixes
    const newTemplate = document.getElementById(
      `${prefix}-2-events-EMPTY_FORM_TEMPLATE`,
    );
    expect(newTemplate).toBeTruthy();
    expect(newTemplate.textContent).toContain(
      'id="id_venues-2-events-__prefix__-DELETE-button"',
    );
    expect(newTemplate.textContent).toContain(
      '<input type="text" name="venues-2-events-__prefix__-name" id="id_venues-2-events-__prefix__-name">',
    );
  });
});
