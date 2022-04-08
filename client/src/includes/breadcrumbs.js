export default function initCollapsibleBreadcrumbs() {
  const breadcrumbsContainer = document.querySelector('[data-breadcrumb-next]');
  const breadcrumbsToggle = breadcrumbsContainer.querySelector(
    '[data-toggle-breadcrumbs]',
  );
  const breadcrumbItems = breadcrumbsContainer.querySelectorAll(
    '[data-breadcrumb-item]',
  );

  const cssClass = {
    maxWidth: 'w-max-w-4xl', // Setting this allows the breadcrumb to animate to this width
  };

  // Local state
  let open = false;
  let mouseExitedToggle = true;

  function hideBreadcrumbs() {
    breadcrumbItems.forEach((breadcrumb) => {
      breadcrumb.classList.remove(cssClass.maxWidth);
      // eslint-disable-next-line no-param-reassign
      breadcrumb.hidden = true;
    });
    breadcrumbsToggle.setAttribute('aria-expanded', 'false');
    // Change Icon to dots
    breadcrumbsToggle
      .querySelector('svg use')
      .setAttribute('href', '#icon-dots-horizontal');
    open = false;
  }

  function showBreadcrumbs() {
    breadcrumbItems.forEach((breadcrumb, index) => {
      setTimeout(() => {
        // eslint-disable-next-line no-param-reassign
        breadcrumb.hidden = false;

        setTimeout(() => {
          breadcrumb.classList.add(cssClass.maxWidth);
        }, 50);
      }, index * 10);
    });
    breadcrumbsToggle.setAttribute('aria-expanded', 'true');
    // Change Icon to cross
    breadcrumbsToggle
      .querySelector('svg use')
      .setAttribute('href', '#icon-cross');
    open = true;
  }

  // Events
  breadcrumbsToggle.addEventListener('click', () => {
    if (open) {
      mouseExitedToggle = false;
      hideBreadcrumbs();
    } else {
      showBreadcrumbs();
    }
  });

  breadcrumbsToggle.addEventListener('mouseenter', () => {
    // If menu is open or the mouse hasn't exited button zone do nothing
    if (open || !mouseExitedToggle) {
      return;
    }

    open = true;
    // Set mouse exited so mouseover doesn't restart until mouse leaves
    mouseExitedToggle = false;
    showBreadcrumbs();
  });

  breadcrumbsContainer.addEventListener('mouseleave', hideBreadcrumbs());
  breadcrumbsToggle.addEventListener('mouseleave', () => {
    mouseExitedToggle = true;
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      hideBreadcrumbs();
    }
  });
}
