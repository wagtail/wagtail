/**
 * Initialise button selectors
 */
const initButtonSelects = () => {
  document.querySelectorAll('.button-select').forEach((element) => {
    const inputElement = element.querySelector(
      'input[type="hidden"]',
    ) as HTMLInputElement;

    if (!inputElement) {
      return;
    }

    element
      .querySelectorAll('.button-select__option')
      .forEach((buttonElement) => {
        buttonElement.addEventListener('click', (event) => {
          event.preventDefault();
          inputElement.value = (buttonElement as HTMLButtonElement).value;

          element
            .querySelectorAll('.button-select__option--selected')
            .forEach((selectedButtonElement) => {
              selectedButtonElement.classList.remove(
                'button-select__option--selected',
              );
            });

          buttonElement.classList.add('button-select__option--selected');
        });
      });
  });
};

export { initButtonSelects };
