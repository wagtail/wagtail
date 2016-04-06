var quoteRegExp = function (str) {
    return (str + '').replace(/[.?*+^$[\]\\(){}|-]/g, "\\$&");
};
var re = new RegExp(quoteRegExp(require("path").sep), "g");

/**
 * Normalize path separators to forward slashes
 * @param path A path in either Windows or POSIX format
 * @returns {string} A path in POSIX format
 */
module.exports = function (path) {
    return ("" + path).replace(re, "/");
};
