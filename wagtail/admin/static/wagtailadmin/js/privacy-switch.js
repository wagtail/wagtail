/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./client/src/entrypoints/admin/privacy-switch.js":
/*!********************************************************!*\
  !*** ./client/src/entrypoints/admin/privacy-switch.js ***!
  \********************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

eval("\nvar __importDefault = (this && this.__importDefault) || function (mod) {\n    return (mod && mod.__esModule) ? mod : { \"default\": mod };\n};\nexports.__esModule = true;\nvar jquery_1 = __importDefault(__webpack_require__(/*! jquery */ \"jquery\"));\n(0, jquery_1[\"default\"])(function () {\n    /* Interface to set permissions from the explorer / editor */\n    // eslint-disable-next-line func-names\n    (0, jquery_1[\"default\"])('[data-a11y-dialog-show=\"set-privacy\"]').on('click', function () {\n        // eslint-disable-next-line no-undef\n        ModalWorkflow({\n            dialogId: 'set-privacy',\n            url: this.getAttribute('data-url'),\n            onload: {\n                set_privacy: function (modal) {\n                    // eslint-disable-next-line func-names\n                    (0, jquery_1[\"default\"])('form', modal.body).on('submit', function () {\n                        modal.postForm(this.action, (0, jquery_1[\"default\"])(this).serialize());\n                        return false;\n                    });\n                    var restrictionTypePasswordField = (0, jquery_1[\"default\"])(\"input[name='restriction_type'][value='password']\", modal.body);\n                    var restrictionTypeGroupsField = (0, jquery_1[\"default\"])(\"input[name='restriction_type'][value='groups']\", modal.body);\n                    var passwordField = (0, jquery_1[\"default\"])('[name=\"password\"]', modal.body).parents('[data-field-wrapper]');\n                    var groupsFields = (0, jquery_1[\"default\"])('#groups-fields', modal.body);\n                    function refreshFormFields() {\n                        if (restrictionTypePasswordField.is(':checked')) {\n                            passwordField.show();\n                            groupsFields.hide();\n                        }\n                        else if (restrictionTypeGroupsField.is(':checked')) {\n                            passwordField.hide();\n                            groupsFields.show();\n                        }\n                        else {\n                            passwordField.hide();\n                            groupsFields.hide();\n                        }\n                    }\n                    refreshFormFields();\n                    (0, jquery_1[\"default\"])(\"input[name='restriction_type']\", modal.body).on('change', refreshFormFields);\n                },\n                set_privacy_done: function (modal, jsonData) {\n                    modal.respond('setPermission', jsonData.is_public);\n                    modal.close();\n                }\n            },\n            responses: {\n                setPermission: function (isPublic) {\n                    if (isPublic) {\n                        // Swap the status sidebar text and icon\n                        (0, jquery_1[\"default\"])('[data-privacy-sidebar-public]').removeClass('w-hidden');\n                        (0, jquery_1[\"default\"])('[data-privacy-sidebar-private]').addClass('w-hidden');\n                        // Swap other privacy indicators in settings and the header live button\n                        (0, jquery_1[\"default\"])('.privacy-indicator').removeClass('private').addClass('public');\n                        (0, jquery_1[\"default\"])('.privacy-indicator-icon use').attr('href', '#icon-view');\n                    }\n                    else {\n                        // Swap the status sidebar text and icon\n                        (0, jquery_1[\"default\"])('[data-privacy-sidebar-public]').addClass('w-hidden');\n                        (0, jquery_1[\"default\"])('[data-privacy-sidebar-private]').removeClass('w-hidden');\n                        // Swap other privacy indicators in settings and the headers live button icon\n                        (0, jquery_1[\"default\"])('.privacy-indicator').removeClass('public').addClass('private');\n                        (0, jquery_1[\"default\"])('.privacy-indicator-icon use').attr('href', '#icon-no-view');\n                    }\n                }\n            }\n        });\n        return false;\n    });\n});\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL3ByaXZhY3ktc3dpdGNoLmpzLmpzIiwibWFwcGluZ3MiOiJBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly93YWd0YWlsLy4vY2xpZW50L3NyYy9lbnRyeXBvaW50cy9hZG1pbi9wcml2YWN5LXN3aXRjaC5qcz8zOGU2Il0sInNvdXJjZXNDb250ZW50IjpbIlwidXNlIHN0cmljdFwiO1xudmFyIF9faW1wb3J0RGVmYXVsdCA9ICh0aGlzICYmIHRoaXMuX19pbXBvcnREZWZhdWx0KSB8fCBmdW5jdGlvbiAobW9kKSB7XG4gICAgcmV0dXJuIChtb2QgJiYgbW9kLl9fZXNNb2R1bGUpID8gbW9kIDogeyBcImRlZmF1bHRcIjogbW9kIH07XG59O1xuZXhwb3J0cy5fX2VzTW9kdWxlID0gdHJ1ZTtcbnZhciBqcXVlcnlfMSA9IF9faW1wb3J0RGVmYXVsdChyZXF1aXJlKFwianF1ZXJ5XCIpKTtcbigwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKGZ1bmN0aW9uICgpIHtcbiAgICAvKiBJbnRlcmZhY2UgdG8gc2V0IHBlcm1pc3Npb25zIGZyb20gdGhlIGV4cGxvcmVyIC8gZWRpdG9yICovXG4gICAgLy8gZXNsaW50LWRpc2FibGUtbmV4dC1saW5lIGZ1bmMtbmFtZXNcbiAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnW2RhdGEtYTExeS1kaWFsb2ctc2hvdz1cInNldC1wcml2YWN5XCJdJykub24oJ2NsaWNrJywgZnVuY3Rpb24gKCkge1xuICAgICAgICAvLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgbm8tdW5kZWZcbiAgICAgICAgTW9kYWxXb3JrZmxvdyh7XG4gICAgICAgICAgICBkaWFsb2dJZDogJ3NldC1wcml2YWN5JyxcbiAgICAgICAgICAgIHVybDogdGhpcy5nZXRBdHRyaWJ1dGUoJ2RhdGEtdXJsJyksXG4gICAgICAgICAgICBvbmxvYWQ6IHtcbiAgICAgICAgICAgICAgICBzZXRfcHJpdmFjeTogZnVuY3Rpb24gKG1vZGFsKSB7XG4gICAgICAgICAgICAgICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICAgICAgICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdmb3JtJywgbW9kYWwuYm9keSkub24oJ3N1Ym1pdCcsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgICAgICAgICAgICAgIG1vZGFsLnBvc3RGb3JtKHRoaXMuYWN0aW9uLCAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSh0aGlzKS5zZXJpYWxpemUoKSk7XG4gICAgICAgICAgICAgICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgICAgICAgICAgICAgIH0pO1xuICAgICAgICAgICAgICAgICAgICB2YXIgcmVzdHJpY3Rpb25UeXBlUGFzc3dvcmRGaWVsZCA9ICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKFwiaW5wdXRbbmFtZT0ncmVzdHJpY3Rpb25fdHlwZSddW3ZhbHVlPSdwYXNzd29yZCddXCIsIG1vZGFsLmJvZHkpO1xuICAgICAgICAgICAgICAgICAgICB2YXIgcmVzdHJpY3Rpb25UeXBlR3JvdXBzRmllbGQgPSAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKShcImlucHV0W25hbWU9J3Jlc3RyaWN0aW9uX3R5cGUnXVt2YWx1ZT0nZ3JvdXBzJ11cIiwgbW9kYWwuYm9keSk7XG4gICAgICAgICAgICAgICAgICAgIHZhciBwYXNzd29yZEZpZWxkID0gKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJ1tuYW1lPVwicGFzc3dvcmRcIl0nLCBtb2RhbC5ib2R5KS5wYXJlbnRzKCdbZGF0YS1maWVsZC13cmFwcGVyXScpO1xuICAgICAgICAgICAgICAgICAgICB2YXIgZ3JvdXBzRmllbGRzID0gKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJyNncm91cHMtZmllbGRzJywgbW9kYWwuYm9keSk7XG4gICAgICAgICAgICAgICAgICAgIGZ1bmN0aW9uIHJlZnJlc2hGb3JtRmllbGRzKCkge1xuICAgICAgICAgICAgICAgICAgICAgICAgaWYgKHJlc3RyaWN0aW9uVHlwZVBhc3N3b3JkRmllbGQuaXMoJzpjaGVja2VkJykpIHtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBwYXNzd29yZEZpZWxkLnNob3coKTtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBncm91cHNGaWVsZHMuaGlkZSgpO1xuICAgICAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgICAgICAgZWxzZSBpZiAocmVzdHJpY3Rpb25UeXBlR3JvdXBzRmllbGQuaXMoJzpjaGVja2VkJykpIHtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBwYXNzd29yZEZpZWxkLmhpZGUoKTtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBncm91cHNGaWVsZHMuc2hvdygpO1xuICAgICAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgICAgICAgZWxzZSB7XG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgcGFzc3dvcmRGaWVsZC5oaWRlKCk7XG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgZ3JvdXBzRmllbGRzLmhpZGUoKTtcbiAgICAgICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgICByZWZyZXNoRm9ybUZpZWxkcygpO1xuICAgICAgICAgICAgICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKShcImlucHV0W25hbWU9J3Jlc3RyaWN0aW9uX3R5cGUnXVwiLCBtb2RhbC5ib2R5KS5vbignY2hhbmdlJywgcmVmcmVzaEZvcm1GaWVsZHMpO1xuICAgICAgICAgICAgICAgIH0sXG4gICAgICAgICAgICAgICAgc2V0X3ByaXZhY3lfZG9uZTogZnVuY3Rpb24gKG1vZGFsLCBqc29uRGF0YSkge1xuICAgICAgICAgICAgICAgICAgICBtb2RhbC5yZXNwb25kKCdzZXRQZXJtaXNzaW9uJywganNvbkRhdGEuaXNfcHVibGljKTtcbiAgICAgICAgICAgICAgICAgICAgbW9kYWwuY2xvc2UoKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9LFxuICAgICAgICAgICAgcmVzcG9uc2VzOiB7XG4gICAgICAgICAgICAgICAgc2V0UGVybWlzc2lvbjogZnVuY3Rpb24gKGlzUHVibGljKSB7XG4gICAgICAgICAgICAgICAgICAgIGlmIChpc1B1YmxpYykge1xuICAgICAgICAgICAgICAgICAgICAgICAgLy8gU3dhcCB0aGUgc3RhdHVzIHNpZGViYXIgdGV4dCBhbmQgaWNvblxuICAgICAgICAgICAgICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJ1tkYXRhLXByaXZhY3ktc2lkZWJhci1wdWJsaWNdJykucmVtb3ZlQ2xhc3MoJ3ctaGlkZGVuJyk7XG4gICAgICAgICAgICAgICAgICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnW2RhdGEtcHJpdmFjeS1zaWRlYmFyLXByaXZhdGVdJykuYWRkQ2xhc3MoJ3ctaGlkZGVuJyk7XG4gICAgICAgICAgICAgICAgICAgICAgICAvLyBTd2FwIG90aGVyIHByaXZhY3kgaW5kaWNhdG9ycyBpbiBzZXR0aW5ncyBhbmQgdGhlIGhlYWRlciBsaXZlIGJ1dHRvblxuICAgICAgICAgICAgICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJy5wcml2YWN5LWluZGljYXRvcicpLnJlbW92ZUNsYXNzKCdwcml2YXRlJykuYWRkQ2xhc3MoJ3B1YmxpYycpO1xuICAgICAgICAgICAgICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJy5wcml2YWN5LWluZGljYXRvci1pY29uIHVzZScpLmF0dHIoJ2hyZWYnLCAnI2ljb24tdmlldycpO1xuICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICAgIGVsc2Uge1xuICAgICAgICAgICAgICAgICAgICAgICAgLy8gU3dhcCB0aGUgc3RhdHVzIHNpZGViYXIgdGV4dCBhbmQgaWNvblxuICAgICAgICAgICAgICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJ1tkYXRhLXByaXZhY3ktc2lkZWJhci1wdWJsaWNdJykuYWRkQ2xhc3MoJ3ctaGlkZGVuJyk7XG4gICAgICAgICAgICAgICAgICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnW2RhdGEtcHJpdmFjeS1zaWRlYmFyLXByaXZhdGVdJykucmVtb3ZlQ2xhc3MoJ3ctaGlkZGVuJyk7XG4gICAgICAgICAgICAgICAgICAgICAgICAvLyBTd2FwIG90aGVyIHByaXZhY3kgaW5kaWNhdG9ycyBpbiBzZXR0aW5ncyBhbmQgdGhlIGhlYWRlcnMgbGl2ZSBidXR0b24gaWNvblxuICAgICAgICAgICAgICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJy5wcml2YWN5LWluZGljYXRvcicpLnJlbW92ZUNsYXNzKCdwdWJsaWMnKS5hZGRDbGFzcygncHJpdmF0ZScpO1xuICAgICAgICAgICAgICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJy5wcml2YWN5LWluZGljYXRvci1pY29uIHVzZScpLmF0dHIoJ2hyZWYnLCAnI2ljb24tbm8tdmlldycpO1xuICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfVxuICAgICAgICB9KTtcbiAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgIH0pO1xufSk7XG4iXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/privacy-switch.js\n");

/***/ }),

/***/ "jquery":
/*!*************************!*\
  !*** external "jQuery" ***!
  \*************************/
/***/ ((module) => {

module.exports = jQuery;

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = __webpack_modules__;
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/chunk loaded */
/******/ 	(() => {
/******/ 		var deferred = [];
/******/ 		__webpack_require__.O = (result, chunkIds, fn, priority) => {
/******/ 			if(chunkIds) {
/******/ 				priority = priority || 0;
/******/ 				for(var i = deferred.length; i > 0 && deferred[i - 1][2] > priority; i--) deferred[i] = deferred[i - 1];
/******/ 				deferred[i] = [chunkIds, fn, priority];
/******/ 				return;
/******/ 			}
/******/ 			var notFulfilled = Infinity;
/******/ 			for (var i = 0; i < deferred.length; i++) {
/******/ 				var [chunkIds, fn, priority] = deferred[i];
/******/ 				var fulfilled = true;
/******/ 				for (var j = 0; j < chunkIds.length; j++) {
/******/ 					if ((priority & 1 === 0 || notFulfilled >= priority) && Object.keys(__webpack_require__.O).every((key) => (__webpack_require__.O[key](chunkIds[j])))) {
/******/ 						chunkIds.splice(j--, 1);
/******/ 					} else {
/******/ 						fulfilled = false;
/******/ 						if(priority < notFulfilled) notFulfilled = priority;
/******/ 					}
/******/ 				}
/******/ 				if(fulfilled) {
/******/ 					deferred.splice(i--, 1)
/******/ 					var r = fn();
/******/ 					if (r !== undefined) result = r;
/******/ 				}
/******/ 			}
/******/ 			return result;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/compat get default export */
/******/ 	(() => {
/******/ 		// getDefaultExport function for compatibility with non-harmony modules
/******/ 		__webpack_require__.n = (module) => {
/******/ 			var getter = module && module.__esModule ?
/******/ 				() => (module['default']) :
/******/ 				() => (module);
/******/ 			__webpack_require__.d(getter, { a: getter });
/******/ 			return getter;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/global */
/******/ 	(() => {
/******/ 		__webpack_require__.g = (function() {
/******/ 			if (typeof globalThis === 'object') return globalThis;
/******/ 			try {
/******/ 				return this || new Function('return this')();
/******/ 			} catch (e) {
/******/ 				if (typeof window === 'object') return window;
/******/ 			}
/******/ 		})();
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/jsonp chunk loading */
/******/ 	(() => {
/******/ 		// no baseURI
/******/ 		
/******/ 		// object to store loaded and loading chunks
/******/ 		// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 		// [resolve, reject, Promise] = chunk loading, 0 = chunk loaded
/******/ 		var installedChunks = {
/******/ 			"privacy-switch": 0
/******/ 		};
/******/ 		
/******/ 		// no chunk on demand loading
/******/ 		
/******/ 		// no prefetching
/******/ 		
/******/ 		// no preloaded
/******/ 		
/******/ 		// no HMR
/******/ 		
/******/ 		// no HMR manifest
/******/ 		
/******/ 		__webpack_require__.O.j = (chunkId) => (installedChunks[chunkId] === 0);
/******/ 		
/******/ 		// install a JSONP callback for chunk loading
/******/ 		var webpackJsonpCallback = (parentChunkLoadingFunction, data) => {
/******/ 			var [chunkIds, moreModules, runtime] = data;
/******/ 			// add "moreModules" to the modules object,
/******/ 			// then flag all "chunkIds" as loaded and fire callback
/******/ 			var moduleId, chunkId, i = 0;
/******/ 			if(chunkIds.some((id) => (installedChunks[id] !== 0))) {
/******/ 				for(moduleId in moreModules) {
/******/ 					if(__webpack_require__.o(moreModules, moduleId)) {
/******/ 						__webpack_require__.m[moduleId] = moreModules[moduleId];
/******/ 					}
/******/ 				}
/******/ 				if(runtime) var result = runtime(__webpack_require__);
/******/ 			}
/******/ 			if(parentChunkLoadingFunction) parentChunkLoadingFunction(data);
/******/ 			for(;i < chunkIds.length; i++) {
/******/ 				chunkId = chunkIds[i];
/******/ 				if(__webpack_require__.o(installedChunks, chunkId) && installedChunks[chunkId]) {
/******/ 					installedChunks[chunkId][0]();
/******/ 				}
/******/ 				installedChunks[chunkId] = 0;
/******/ 			}
/******/ 			return __webpack_require__.O(result);
/******/ 		}
/******/ 		
/******/ 		var chunkLoadingGlobal = globalThis["webpackChunkwagtail"] = globalThis["webpackChunkwagtail"] || [];
/******/ 		chunkLoadingGlobal.forEach(webpackJsonpCallback.bind(null, 0));
/******/ 		chunkLoadingGlobal.push = webpackJsonpCallback.bind(null, chunkLoadingGlobal.push.bind(chunkLoadingGlobal));
/******/ 	})();
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module depends on other loaded chunks and execution need to be delayed
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["wagtail/admin/static/wagtailadmin/js/vendor"], () => (__webpack_require__("./client/src/entrypoints/admin/privacy-switch.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;