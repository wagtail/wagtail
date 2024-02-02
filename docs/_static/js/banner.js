/**
 * Wagtail banner script
 */
(function initBanner() {
  /**
   * Util to write a cookie.
   *
   * @param {string} name
   * @param {string} value
   * @param {number} days
   * @returns {void}
   */
  function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);

    document.cookie = [
      [encodeURIComponent(name), '=', encodeURIComponent(value), ';'].join(''),
      'SameSite=Strict;',
      ['expires=', date.toGMTString()].join(''),
    ].join(' ');
  }

  /**
   * Util to check if the cookie is written.
   *
   * @param {string} name
   * @param {string} value
   * @returns {boolean}
   */
  function hasCookie(name, value) {
    return document.cookie.split('; ').indexOf(name + '=' + value) >= 0;
  }

  const MINIMUM_COOKIE_DURATION = 30;

  /**
   * Creates the promotion banner based on the element in the DOM.
   *
   * @returns {void}
   */
  function createBanner() {
    const template = document.querySelector('[data-promotion-banner]');
    if (!template) return;
    const dateUntil = new Date(template.dataset.dateUntil || 'INACTIVE');
    if (!(dateUntil instanceof Date) || Number.isNaN(dateUntil.valueOf())) {
      return;
    }

    // Pause any promotional banner for X days when manually cleared
    const cookieDuration = Math.max(
      Number(template.dataset.clearDuration || MINIMUM_COOKIE_DURATION),
      MINIMUM_COOKIE_DURATION,
    );

    // Create a cookie name that is unique for this specific promotion's expiry
    const cookieName =
      'WAGTAIL_PROMOTION_BANNER_CLEARED_' +
      dateUntil.toISOString().substring(0, 10).replaceAll('-', '_');

    if (!hasCookie(cookieName, 'true') && new Date() < dateUntil) {
      const promotionBanner =
        template.content.firstElementChild.cloneNode(true);

      promotionBanner
        .querySelector('[data-clear]')
        // eslint-disable-next-line prefer-arrow-callback
        .addEventListener('click', function handleClose() {
          setCookie(cookieName, 'true', cookieDuration);
          promotionBanner.remove();
        });

      document.querySelector('main').prepend(promotionBanner);
    }
  }

  document.addEventListener('DOMContentLoaded', createBanner);
})();
