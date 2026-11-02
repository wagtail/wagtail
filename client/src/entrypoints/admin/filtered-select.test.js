import { initFilteredSelect } from './filtered-select';

describe('filtered-select', () => {
  const HTML = `
    <div>
      <select id="id_continent">
        <option value="">--------</option>
        <option value="1">Europe</option>
        <option value="2">Africa</option>
        <option value="3">Asia</option>
      </select>
    </div>
    <div>
      <select id="id_country" data-widget="filtered-select" data-filter-field="id_continent">
        <option value="">--------</option>
        <option value="1" data-filter-value="3">China</option>
        <option value="2" data-filter-value="2">Egypt</option>
        <option value="3" data-filter-value="1">France</option>
        <option value="4" data-filter-value="1">Germany</option>
        <option value="5" data-filter-value="3">Japan</option>
        <option value="6" data-filter-value="1,3">Russia</option>
        <option value="7" data-filter-value="2">South Africa</option>
        <option value="8" data-filter-value="1,3">Turkey</option>
        <option value="9">Unfiltered Country</option>
      </select>
    </div>
  `;

  let sourceSelect;
  let targetSelect;

  beforeEach(() => {
    document.body.innerHTML = HTML;
    sourceSelect = document.getElementById('id_continent');
    targetSelect = document.getElementById('id_country');
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('does nothing if the source filter field does not exist', () => {
    targetSelect.dataset.filterField = 'non-existent-field';
    expect(() => {
      initFilteredSelect(targetSelect);
    }).not.toThrow();
  });

  it('shows all options when no filter is selected initially', () => {
    initFilteredSelect(targetSelect);

    const values = Array.from(targetSelect.options).map((opt) => opt.value);
    expect(values).toEqual(['', '1', '2', '3', '4', '5', '6', '7', '8', '9']);
  });

  it('filters options when the source select changes', () => {
    initFilteredSelect(targetSelect);

    // Select "Asia" (value 3)
    sourceSelect.value = '3';
    sourceSelect.dispatchEvent(new Event('change'));

    const values = Array.from(targetSelect.options).map((opt) => opt.value);
    // Should include blank '', China (1), Japan (5), Russia (6), Turkey (8)
    expect(values).toEqual(['', '1', '5', '6', '8']);

    const labels = Array.from(targetSelect.options).map(
      (opt) => opt.textContent,
    );
    expect(labels).toEqual(['--------', 'China', 'Japan', 'Russia', 'Turkey']);
  });

  it('preserves current target value if it matches the new filter', () => {
    initFilteredSelect(targetSelect);

    // Select China (value 1, filterValue 3)
    targetSelect.value = '1';

    // Filter by Asia (value 3)
    sourceSelect.value = '3';
    sourceSelect.dispatchEvent(new Event('change'));

    expect(targetSelect.value).toBe('1');
  });

  it('resets target value to empty if it does not match the new filter', () => {
    initFilteredSelect(targetSelect);

    // Select France (value 3, filterValue 1)
    targetSelect.value = '3';

    // Filter by Africa (value 2)
    sourceSelect.value = '2';
    sourceSelect.dispatchEvent(new Event('change'));

    expect(targetSelect.value).toBe('');
    const values = Array.from(targetSelect.options).map((opt) => opt.value);
    expect(values).toEqual(['', '2', '7']);
  });

  it('shows all options again when source select is cleared back to empty', () => {
    initFilteredSelect(targetSelect);

    sourceSelect.value = '2';
    sourceSelect.dispatchEvent(new Event('change'));
    expect(targetSelect.options.length).toBe(3);

    // Clear filter
    sourceSelect.value = '';
    sourceSelect.dispatchEvent(new Event('change'));
    expect(targetSelect.options.length).toBe(10);
  });
});
