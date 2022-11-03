/**
 * Initialise button selectors
 */
 function initButtonSelects() {
    document.querySelectorAll('.button-select').forEach((element) => {
      const inputElement = element.querySelector(
        'input[type="hidden"]',
      ) as HTMLInputElement;
  
      element
        .querySelectorAll('.button-select__option')
        .forEach((buttonElement) => {
          buttonElement.addEventListener('click', (e) => {
            e.preventDefault();
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
  }
  
  export { initButtonSelects };
  