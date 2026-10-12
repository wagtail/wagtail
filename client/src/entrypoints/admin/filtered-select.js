/* A select box component that can be dynamically filtered by the option chosen in another select box.

  <div>
    <label for="id_continent">Continent</label>
    <select id="id_continent">
      <option value="">--------</option>
      <option value="1">Europe</option>
      <option value="2">Africa</option>
      <option value="3">Asia</option>
    </select>
  </div>
  <div>
    <label for="id_country">Country</label>
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
    </select>
  </div>
*/

import { domReady } from '../../utils/domReady';

function initFilteredSelect(targetSelect) {
  const sourceSelect = document.getElementById(
    targetSelect.dataset.filterField,
  );
  if (!sourceSelect) return;

  const optionData = Array.from(targetSelect.options).map((option) => {
    let filterValue;
    if ('filterValue' in option.dataset) {
      filterValue = option.dataset.filterValue.split(',');
    } else {
      filterValue = [];
    }

    return {
      value: option.value,
      label: option.label || option.text || option.textContent,
      filterValue,
    };
  });

  function updateFromSource() {
    const currentValue = targetSelect.value;
    targetSelect.innerHTML = '';
    const chosenFilter = sourceSelect.value;
    let filteredValues;

    if (chosenFilter === '') {
      /* no filter selected - show all options */
      filteredValues = optionData;
    } else {
      filteredValues = optionData.filter(
        (option) =>
          option.value === '' || option.filterValue.includes(chosenFilter),
      );
    }

    let foundValue = false;
    filteredValues.forEach((filtered) => {
      const option = document.createElement('option');
      option.value = filtered.value;
      if (filtered.value === currentValue) {
        foundValue = true;
      }
      option.textContent = filtered.label;
      targetSelect.appendChild(option);
    });

    if (foundValue) {
      targetSelect.value = currentValue;
    } else {
      targetSelect.value = '';
    }
  }

  updateFromSource();
  sourceSelect.addEventListener('change', updateFromSource);
}

domReady().then(() => {
  document
    .querySelectorAll('[data-widget="filtered-select"]')
    .forEach(initFilteredSelect);
});

export { initFilteredSelect };
