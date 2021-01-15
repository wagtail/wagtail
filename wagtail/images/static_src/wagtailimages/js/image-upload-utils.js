(function () {
  /**
   * Default implementation of converting an image filename into a
   * suitable title that will remove the file extension.
   * Note: using prototype.call for better debugging stack.
   *
   * @param {string} str
   * @returns {string}
   */
  function getImageUploadTitle(str) {
    return String.prototype.replace.call(str, /\.[^\.]+$/, "");
  }

  window.wagtail.utils.getImageUploadTitle = getImageUploadTitle;
})();
