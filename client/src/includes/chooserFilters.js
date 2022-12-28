// Toggle Modal Search filters on or off by default or use 'on' or 'off' to manually set the state.
class ChooserFilter {
  constructor(toggleButton) {
    this.toggleButton = toggleButton;
    this.filters = document.querySelector(`#${this.toggleButton.getAttribute('aria-controls')}`);
    this.toggleHandler = this.toggle.bind(this)
    this.bindEvents()
  }

  bindEvents() {
    this.toggleButton.addEventListener('click', this.toggleHandler);

    document.addEventListener('wagtail:ajaxify-chooser-links', () => {
      this.toggleButton.removeEventListener('click', this.toggleHandler)
    })
  }

  onToggle() {
    this.toggleButton.dispatchEvent(
      new CustomEvent('wagtail:toggle-chooser-filters', {
        bubbles: true,
        cancelable: false,
        detail: {hidden: this.hidden()},
      }),
    )
  }

  hidden() {
    return this.filters.getAttribute('aria-hidden') === 'true';
  }

  hide() {
    this.filters.setAttribute('aria-hidden', 'true');
    this.toggleButton.classList.remove('active');
    this.onToggle();
  }

  show() {
    this.filters.setAttribute('aria-hidden', 'false');
    this.toggleButton.classList.add('active');
    this.onToggle();
  }

  toggle() {
    this.hidden() ? this.show() : this.hide();
  }
}

const initChooserFilters = (filters = document.querySelectorAll('[data-chooser-filter-toggle]')) => {
  filters.forEach((filter) => {
    new ChooserFilter(filter);
  })
}


export default initChooserFilters;
