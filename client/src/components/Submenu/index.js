/**
 * Initialises the Submenus within the primary Wagtail menu (excluding the Explorer menu)
 */

const initSubmenus = () => {
  const primaryNavContainer = document.querySelector('[data-nav-primary]');

  if (!primaryNavContainer) {
    return;
  }

  const subMenus = document.querySelectorAll('[data-nav-primary-submenu-trigger]');
  const activeClass = 'submenu-active';

  subMenus.forEach(subMenu => {
    subMenu.addEventListener('click', e => {
      primaryNavContainer.classList.remove(activeClass);
      subMenus.forEach(subMenu => subMenu.classList.remove(activeClass));

      primaryNavContainer.classList.toggle(activeClass);
      subMenu.parentNode.classList.toggle(activeClass);

      document.addEventListener('mousedown', e => {
        if (!subMenu.contains(e.target) && subMenu !== e.target) {
          primaryNavContainer.classList.remove(activeClass);
          subMenu.parentNode.classList.remove(activeClass);
        }
      });

      document.addEventListener('keydown', e => {
        if (e.keyCode == 27) {
          primaryNavContainer.classList.remove(activeClass);
          subMenu.parentNode.classList.remove(activeClass);
        }
      });

      e.preventDefault();
    });
  });
};

export { initSubmenus };
