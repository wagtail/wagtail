const initSkipLink = () => {
  // Inspired by https://github.com/selfthinker/dokuwiki_template_writr/blob/master/js/skip-link-focus-fix.js

  const skiplink = document.querySelector('[data-skiplink]');
  const main = document.querySelector('main');

  const handleBlur = () => {
    if (!main) return;
    main.removeAttribute ('tabindex');
    main.removeEventListener('blur', handleBlur);
    main.removeEventListener('focusout', handleBlur);
  };

  const handleClick = () => {
    if (!main) return;
    main.setAttribute('tabindex', "-1");
    main.addEventListener('blur', handleBlur);
    main.addEventListener('focusout', handleBlur);
    main.focus();
  };

  if (skiplink && main) {
    skiplink.addEventListener('click', handleClick);
  }
};

export default initSkipLink;
