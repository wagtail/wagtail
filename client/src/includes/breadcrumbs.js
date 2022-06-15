export default function initCollapsibleBreadcrumbs() {
  const breadcrumbsContainer = document.querySelector('[data-breadcrumb-next]');

  if (!breadcrumbsContainer) {
    return;
  }

  const header = breadcrumbsContainer.closest(
    breadcrumbsContainer.dataset.headerSelector || 'header',
  );

  if (!header) return;

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
  let keepOpen = false;
  let hideBreadcrumbsWithDelay;

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
      .setAttribute('href', '#icon-breadcrumb-expand');
    open = false;
    keepOpen = false;

    document.dispatchEvent(new CustomEvent('wagtail:breadcrumbs-collapse'));
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
    open = true;

    document.dispatchEvent(new CustomEvent('wagtail:breadcrumbs-expand'));
  }

  breadcrumbsToggle.addEventListener('keydown', (e) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();

      if (keepOpen || open) {
        hideBreadcrumbs();
      } else {
        showBreadcrumbs();
        keepOpen = true;

        // Change Icon to cross
        breadcrumbsToggle
          .querySelector('svg use')
          .setAttribute('href', '#icon-cross');
      }
    }
  });

  // Events
  breadcrumbsToggle.addEventListener('click', () => {
    if (keepOpen) {
      mouseExitedToggle = false;
      hideBreadcrumbs();
    }

    if (open) {
      mouseExitedToggle = false;
      keepOpen = true;

      // Change Icon to cross
      breadcrumbsToggle
        .querySelector('svg use')
        .setAttribute('href', '#icon-cross');
    } else if (mouseExitedToggle) {
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

  breadcrumbsToggle.addEventListener('mouseleave', () => {
    mouseExitedToggle = true;
  });

  header.addEventListener('mouseleave', () => {
    if (!keepOpen) {
      hideBreadcrumbsWithDelay = setTimeout(() => {
        hideBreadcrumbs();
        //  Give a little bit of time before closing in case the user changes their mind
      }, 500);
    }
  });

  header.addEventListener('mouseenter', () => {
    clearTimeout(hideBreadcrumbsWithDelay);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      hideBreadcrumbs();
    }
  });
}
