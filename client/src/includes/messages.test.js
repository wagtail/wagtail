import { initButtonSelects } from './initButtonSelects';

// save our DOM elements to a variable
const testElements = `
<div class = "button-select">
  <input type="hidden" value/>
  <button class="button-select__option" value>
    All
  </button>
  <button class="button-select__option" value = "true">
    Awaiting my review
  </button>
</div>

<div class="button-select">
  <input type="hidden" value />
  <button class="button-select__option" value>
    All
  </button>
  <button class="button-select__option" value="in_progress">
    In Progress
  </button>
  <button class="button-select__option" value="approved">
    Approved
  </button>
  <button class="button-select__option" value="needs_changes">
    Needs changes
  </button>
  <button class="button-select__option" value="cancelled">
    Cancelled
  </button>
</div>
`;

describe('initButtonSelects', () => {
  const spy = jest.spyOn(document, 'addEventListener');

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should do nothing if there is no button-select container', () => {
    // Set up our document body
    document.body.innerHTML = `
    <div>
      <input type="hidden" />
      <button class="button-select__option" />
    </div>`;
    initButtonSelects();
    // no event listeners registered
    expect(spy).not.toHaveBeenCalled();
  });

  describe('there is a button-select container present', () => {
    it('should add class of button-select__option--selected to button-select__option when clicked', () => {
      document.body.innerHTML = testElements;
      initButtonSelects();
      // select all the buttons with the class
      document.querySelectorAll('.button-select__option').forEach((button) => {
        button.click();
        expect(button.classList.value).toContain(
          'button-select__option--selected',
        );
      });
    });

    it('should remove the class button-select__option--selected when button is not clicked', () => {
      document.body.innerHTML = testElements;
      initButtonSelects();
      document.querySelectorAll('.button-select').forEach((element) => {
        element.querySelectorAll('.button-select__option').forEach((button) => {
          button.click();
          element
            .querySelectorAll('.button-select__option--selected')
            .forEach((selectedButtonElement) => {
              selectedButtonElement.classList.remove(
                'button-select__option--selected',
              );
            });
          expect(button.classList.value).not.toContain(
            'button-select__option--selected',
          );
        });
      });
    });
    it('add the value of the button clicked to the input', () => {
      document.body.innerHTML = testElements;
      initButtonSelects();
      document.querySelectorAll('.button-select__option').forEach((button) => {
        button.click();

        const inputElement = document.querySelector('input[type="hidden"]');
        inputElement.value = button.value;

        expect(inputElement.value).toEqual(button.value);
      });
    });
  });
});
