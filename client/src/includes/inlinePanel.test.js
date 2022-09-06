describe('inlinePanel', () => {
  let buildExpandingFormsetMock;
  let inlinePanel;
  let onAdd;

  beforeAll(() => {
    // ensure we mock the global buildExpandingFormset before importing

    buildExpandingFormsetMock = jest.fn();
    window.buildExpandingFormset = buildExpandingFormsetMock;

    inlinePanel = require('./inlinePanel').inlinePanel;

    document.body.innerHTML = `
<form>
    <input name="person_cafe_relationship-TOTAL_FORMS" value="0" id="id_person_cafe_relationship-TOTAL_FORMS" type="hidden" />
    <input name="person_cafe_relationship-INITIAL_FORMS" value="0" id="id_person_cafe_relationship-INITIAL_FORMS" type="hidden" />
    <input name="person_cafe_relationship-MIN_NUM_FORMS" value="1" id="id_person_cafe_relationship-MIN_NUM_FORMS" type="hidden" />
    <input name="person_cafe_relationship-MAX_NUM_FORMS" value="5" id="id_person_cafe_relationship-MAX_NUM_FORMS" type="hidden" />
    <div id="id_person_cafe_relationship-FORMS"></div>
</form>`;
  });

  it('should call the buildExpandingFormset with correct prefix & an onAdd function', () => {
    expect(buildExpandingFormsetMock).not.toHaveBeenCalled();

    const options = {
      formsetPrefix: 'person_cafe_relationship',
      emptyChildFormPrefix: 'person_cafe_relationship-__prefix__',
      onAdd: jest.fn(),
    };

    inlinePanel(options);

    expect(buildExpandingFormsetMock).toHaveBeenCalledWith(
      options.formsetPrefix,
      { onAdd: expect.any(Function) },
    );

    onAdd = buildExpandingFormsetMock.mock.calls[0][1].onAdd;

    expect(options.onAdd).not.toHaveBeenCalled();

    // fake the buildExpandingFormset onAdd callback
    const count = 0;
    onAdd(count);

    // check that any onAdd function getting passed into options gets called
    expect(options.onAdd).toHaveBeenCalled();
  });
});
