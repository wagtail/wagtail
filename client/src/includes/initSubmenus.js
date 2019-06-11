/**
 * Initialises the Submenus within the primary Wagtail menu (excluding the Explorer menu)
 */

const initSubmenus = () => {
  const primaryNavContainer = document.querySelector('[data-nav-primary]');

  if (!primaryNavContainer) {
    return;
  }

  const subMenuTriggers = document.querySelectorAll(
    '[data-nav-primary-submenu-trigger]'
  );
  const activeClass = 'submenu-active';

  [...subMenuTriggers].forEach(subMenuTrigger => {
    subMenuTrigger.addEventListener('click', clickEvent => {
      const submenuContainer = subMenuTrigger.parentNode;

      primaryNavContainer.classList.remove(activeClass);
      [...subMenuTriggers].forEach(sm => sm.classList.remove(activeClass));

      primaryNavContainer.classList.toggle(activeClass);
      submenuContainer.classList.toggle(activeClass);

      document.addEventListener('mousedown', e => {
        if (
          !submenuContainer.contains(e.target) &&
          subMenuTrigger !== e.target
        ) {
          primaryNavContainer.classList.remove(activeClass);
          submenuContainer.classList.remove(activeClass);
        }
      });

      document.addEventListener('keydown', e => {
        // IE11 uses "Esc" instead of "Escape"
        if (e.key === 'Escape' || e.key === 'Esc') {
          primaryNavContainer.classList.remove(activeClass);
          submenuContainer.classList.remove(activeClass);
        }
      });

      clickEvent.preventDefault();
    });
  });
};

export { initSubmenus };
