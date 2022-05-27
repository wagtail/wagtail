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
    const COOKIE_NAME = 'WAGTAIL_PROMOTION_BANNER_CLOSED';
    const promotionBanner = template.content.firstElementChild.cloneNode(true);

    if (!hasCookie(COOKIE_NAME, 'true') && new Date() < dateUntil) {
      promotionBanner
        .querySelector('[data-close]')
        .addEventListener('click', () => {
          // pause any promotional banner for X days
          setCookie(COOKIE_NAME, 'true', 30);
          promotionBanner.remove();
        });

      document.querySelector('main').prepend(promotionBanner);
    }
  }

  document.addEventListener('DOMContentLoaded', createBanner);
})();
