import { Controller } from '@hotwired/stimulus';

export class BreadcrumbsController extends Controller {
  static targets = ['w-breadcrumbs', 'toggle'];
  private toggleTarget!: HTMLElement;
  private breadcrumbsTargets!: Element[];
  
  private open = false;
  private mouseExitedToggle = true;
  private keepOpen = false;

  private cssClass = {
    maxWidth: 'w-max-w-4xl', // Setting this allows the breadcrumb to animate to this width
  };

  connect(): void {
    const header = this.element.closest(this.data.get('headerSelector') || 'header');

    if (!header) {
      return;
    }

    const breadcrumbsToggle = this.toggleTarget;

    const breadcrumbItems = this.breadcrumbsTargets;

    breadcrumbItems.forEach((breadcrumb) => {
      breadcrumb.classList.remove(this.cssClass.maxWidth);
      breadcrumb.hidden = true;
    });

    breadcrumbsToggle.setAttribute('aria-expanded', 'false');

    breadcrumbsToggle
      .querySelector('svg use')
      .setAttribute('href', '#icon-breadcrumb-expand');

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.hideBreadcrumbs();
      }
    });
  }

  toggleBreadcrumbs(): void {
    const breadcrumbsToggle = this.toggleTarget;
    const breadcrumbItems = this.breadcrumbsTargets;

    if (this.keepOpen || this.open) {
      this.hideBreadcrumbs();
    } else {
      this.showBreadcrumbs();
      this.keepOpen = true;

      // Change Icon to cross
      breadcrumbsToggle
        .querySelector('svg use')
        .setAttribute('href', '#icon-cross');
    }
  }

  hideBreadcrumbs(): void {
    const breadcrumbItems = this.breadcrumbsTargets;
    const breadcrumbsToggle = this.toggleTarget;

    breadcrumbItems.forEach((breadcrumb) => {
      breadcrumb.classList.remove(this.cssClass.maxWidth);
      breadcrumb.hidden = true;
    });

    breadcrumbsToggle.setAttribute('aria-expanded', 'false');

    // Change Icon to dots
    breadcrumbsToggle
      .querySelector('svg use')
      .setAttribute('href', '#icon-breadcrumb-expand');

    this.open = false;
    this.keepOpen = false;

    document.dispatchEvent(new CustomEvent('wagtail:breadcrumbs-collapse'));
  }

  showBreadcrumbs(): void {
    const breadcrumbItems = this.breadcrumbsTargets;
    const breadcrumbsToggle = this.toggleTarget;

    breadcrumbItems.forEach((breadcrumb) => {
      breadcrumb.hidden = false;
      breadcrumb.classList.add(this.cssClass.maxWidth);
    });

    breadcrumbsToggle.setAttribute('aria-expanded', 'true');

    this.open = true;

    document.dispatchEvent(new CustomEvent('wagtail:breadcrumbs-expand'));
  }

  onMouseEnter(): void {
    const breadcrumbsToggle = this.toggleTarget;
    const breadcrumbItems = this.breadcrumbsTargets;

    if (this.open || !this.mouseExitedToggle) {
      return;
    }

    this.open = true;

    // Set mouse exited so mouseover doesn't restart until mouse leaves
    this.mouseExitedToggle = false;

    breadcrumbItems.forEach((breadcrumb) => {
      breadcrumb.hidden = false;
      breadcrumb.classList.add(this.cssClass.maxWidth);
    });

    breadcrumbsToggle
      .querySelector('svg use')
      .setAttribute('href', '#icon-cross');
  }

  onMouseLeave(): void {
    this.mouseExitedToggle = true;
  }

  onHeaderMouseLeave(): void {
    if (!this.keepOpen) {
      this.hideBreadcrumbs();
    }
  }
}