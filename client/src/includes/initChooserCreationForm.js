class ChooserCreationForm {
  constructor(node) {
    this.container = node;
    this.parent = this.container.closest('[data-chooser-with-creation-form]')
    this.formBackButton = this.container.querySelector('[data-chooser-form-back]');
    this.showFormButtons = this.container.querySelectorAll('[data-chooser-form-toggle]');
    this.chooserFormWrapper = this.container.querySelector('[data-chooser-creation-form-wrapper]');
    this.chooserForm = this.container.querySelector('[data-chooser-creation-form]');
    this.chooserBody = this.container.querySelector('[data-chooser-body]');
    this.headerHeight = this.chooserFormWrapper.querySelector('.w-chooser-header').offsetHeight;

    // Set the chooserBody min-height to animate later
    this.parent.style.minHeight = '0'
    // Set chooserform to be invisible so it can't be tabbed to
    this.chooserFormWrapper.classList.add('w-invisible');
    // this.parent.style.minHeight = `${this.chooserBody.offsetHeight}px`

    this.toggleFormHandler = this.toggleForm.bind(this);
    this.bindEvents();
  }

  bindEvents() {
    if (this.showFormButtons) {
      this.showFormButtons.forEach((button) => {
        button.addEventListener('click', this.toggleFormHandler);

        document.addEventListener('wagtail:ajaxify-chooser-links', () => {
          button.removeEventListener('click', this.toggleFormHandler)
        })
      });
    }

    if (this.formBackButton) {
      this.formBackButton.addEventListener('click', this.toggleFormHandler);

      document.addEventListener('wagtail:ajaxify-chooser-links', () => {
        this.formBackButton.removeEventListener('click', this.toggleFormHandler)
      })
    }

    this.container.addEventListener('wagtail:toggle-chooser-filters', (e) => {
      // When filters are closed if the height isn't right then reset it
      // This fixes a scenario when a user reveals the creation form with the filters enabled and then comes back to the chooserBody and turns them off
      // e.detail.hidden && (this.parent.style.maxHeight = `${this.chooserBody.offsetHeight}px`)
    })

  }

  showForm = () => {
    this.chooserFormWrapper.setAttribute('aria-hidden', 'false');
    this.chooserFormWrapper.classList.remove('w-invisible');
    this.chooserBody.setAttribute('aria-hidden', 'true');

    // Set the height of the dialog to the forms height
    this.parent.style.minHeight = `${this.chooserForm.offsetHeight + this.headerHeight}px`

    setTimeout(() => {
      this.chooserBody.classList.add('w-invisible');
    }, 600);
  }

  hideForm = () => {
    this.chooserBody.setAttribute('aria-hidden', 'false');
    this.chooserBody.classList.remove('w-invisible');

    this.chooserFormWrapper.setAttribute('aria-hidden', 'true');
    setTimeout(() => {
      this.chooserFormWrapper.classList.add('w-invisible');
    }, 600)

    // Reset dialog height back to original
    this.parent.style.minHeight = '0'
  }

  formIsHidden = () => {
    return this.chooserFormWrapper.getAttribute('aria-hidden') === 'true'
  }

  toggleForm = () => {
    this.formIsHidden() ? this.showForm() : this.hideForm()

    this.chooserFormWrapper.dispatchEvent(
      new CustomEvent('wagtail:toggle-chooser-creation-form', {
        bubbles: true,
        detail: {hidden: this.formIsHidden()}
      }),
    )
  }
}

const initChooserCreationForm = (chooserFormWrapperContainers = document.querySelectorAll('[data-chooser-with-creation-form]')) => {
  chooserFormWrapperContainers.forEach((container) => {
    new ChooserCreationForm(container)
  })
}

export default initChooserCreationForm;
