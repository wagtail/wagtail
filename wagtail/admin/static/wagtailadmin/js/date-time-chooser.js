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

/***/ "./client/src/entrypoints/admin/date-time-chooser.js":
/*!***********************************************************!*\
  !*** ./client/src/entrypoints/admin/date-time-chooser.js ***!
  \***********************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

eval("\nvar __importDefault = (this && this.__importDefault) || function (mod) {\n    return (mod && mod.__esModule) ? mod : { \"default\": mod };\n};\nexports.__esModule = true;\nvar jquery_1 = __importDefault(__webpack_require__(/*! jquery */ \"jquery\"));\n/* global wagtailConfig */\njquery_1[\"default\"].fn.datetimepicker.defaults.i18n.wagtail_custom_locale = {\n    months: wagtailConfig.STRINGS.MONTHS,\n    dayOfWeek: wagtailConfig.STRINGS.WEEKDAYS,\n    dayOfWeekShort: wagtailConfig.STRINGS.WEEKDAYS_SHORT\n};\njquery_1[\"default\"].datetimepicker.setLocale('wagtail_custom_locale');\n// Compare two date objects. Ignore minutes and seconds.\nfunction dateEqual(x, y) {\n    return (x.getDate() === y.getDate() &&\n        x.getMonth() === y.getMonth() &&\n        x.getYear() === y.getYear());\n}\nwindow.dateEqual = dateEqual;\n/*\nRemove the xdsoft_current css class from markup unless the selected date is currently in view.\nKeep the normal behaviour if the home button is clicked.\n */\nfunction hideCurrent(current, input) {\n    var selected = new Date(input[0].value);\n    if (!dateEqual(selected, current)) {\n        (0, jquery_1[\"default\"])(this)\n            .find('.xdsoft_datepicker .xdsoft_current:not(.xdsoft_today)')\n            .removeClass('xdsoft_current');\n    }\n}\nwindow.hideCurrent = hideCurrent;\nfunction initDateChooser(id, opts) {\n    if (window.dateTimePickerTranslations) {\n        (0, jquery_1[\"default\"])('#' + id).datetimepicker(jquery_1[\"default\"].extend({\n            closeOnDateSelect: true,\n            timepicker: false,\n            scrollInput: false,\n            format: 'Y-m-d',\n            onGenerate: hideCurrent,\n            onChangeDateTime: function (_, $el) {\n                $el.get(0).dispatchEvent(new Event('change'));\n            }\n        }, opts || {}));\n    }\n    else {\n        (0, jquery_1[\"default\"])('#' + id).datetimepicker(jquery_1[\"default\"].extend({\n            timepicker: false,\n            scrollInput: false,\n            format: 'Y-m-d',\n            onGenerate: hideCurrent,\n            onChangeDateTime: function (_, $el) {\n                $el.get(0).dispatchEvent(new Event('change'));\n            }\n        }, opts || {}));\n    }\n}\nwindow.initDateChooser = initDateChooser;\nfunction initTimeChooser(id, opts) {\n    if (window.dateTimePickerTranslations) {\n        (0, jquery_1[\"default\"])('#' + id).datetimepicker(jquery_1[\"default\"].extend({\n            closeOnDateSelect: true,\n            datepicker: false,\n            scrollInput: false,\n            format: 'H:i',\n            onChangeDateTime: function (_, $el) {\n                $el.get(0).dispatchEvent(new Event('change'));\n            }\n        }, opts || {}));\n    }\n    else {\n        (0, jquery_1[\"default\"])('#' + id).datetimepicker(jquery_1[\"default\"].extend({\n            datepicker: false,\n            format: 'H:i',\n            onChangeDateTime: function (_, $el) {\n                $el.get(0).dispatchEvent(new Event('change'));\n            }\n        }, opts || {}));\n    }\n}\nwindow.initTimeChooser = initTimeChooser;\nfunction initDateTimeChooser(id, opts) {\n    if (window.dateTimePickerTranslations) {\n        (0, jquery_1[\"default\"])('#' + id).datetimepicker(jquery_1[\"default\"].extend({\n            closeOnDateSelect: true,\n            format: 'Y-m-d H:i',\n            scrollInput: false,\n            onGenerate: hideCurrent,\n            onChangeDateTime: function (_, $el) {\n                $el.get(0).dispatchEvent(new Event('change'));\n            }\n        }, opts || {}));\n    }\n    else {\n        (0, jquery_1[\"default\"])('#' + id).datetimepicker(jquery_1[\"default\"].extend({\n            format: 'Y-m-d H:i',\n            onGenerate: hideCurrent,\n            onChangeDateTime: function (_, $el) {\n                $el.get(0).dispatchEvent(new Event('change'));\n            }\n        }, opts || {}));\n    }\n}\nwindow.initDateTimeChooser = initDateTimeChooser;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL2RhdGUtdGltZS1jaG9vc2VyLmpzLmpzIiwibWFwcGluZ3MiOiJBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSIsInNvdXJjZXMiOlsid2VicGFjazovL3dhZ3RhaWwvLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL2RhdGUtdGltZS1jaG9vc2VyLmpzPzJiZDAiXSwic291cmNlc0NvbnRlbnQiOlsiXCJ1c2Ugc3RyaWN0XCI7XG52YXIgX19pbXBvcnREZWZhdWx0ID0gKHRoaXMgJiYgdGhpcy5fX2ltcG9ydERlZmF1bHQpIHx8IGZ1bmN0aW9uIChtb2QpIHtcbiAgICByZXR1cm4gKG1vZCAmJiBtb2QuX19lc01vZHVsZSkgPyBtb2QgOiB7IFwiZGVmYXVsdFwiOiBtb2QgfTtcbn07XG5leHBvcnRzLl9fZXNNb2R1bGUgPSB0cnVlO1xudmFyIGpxdWVyeV8xID0gX19pbXBvcnREZWZhdWx0KHJlcXVpcmUoXCJqcXVlcnlcIikpO1xuLyogZ2xvYmFsIHdhZ3RhaWxDb25maWcgKi9cbmpxdWVyeV8xW1wiZGVmYXVsdFwiXS5mbi5kYXRldGltZXBpY2tlci5kZWZhdWx0cy5pMThuLndhZ3RhaWxfY3VzdG9tX2xvY2FsZSA9IHtcbiAgICBtb250aHM6IHdhZ3RhaWxDb25maWcuU1RSSU5HUy5NT05USFMsXG4gICAgZGF5T2ZXZWVrOiB3YWd0YWlsQ29uZmlnLlNUUklOR1MuV0VFS0RBWVMsXG4gICAgZGF5T2ZXZWVrU2hvcnQ6IHdhZ3RhaWxDb25maWcuU1RSSU5HUy5XRUVLREFZU19TSE9SVFxufTtcbmpxdWVyeV8xW1wiZGVmYXVsdFwiXS5kYXRldGltZXBpY2tlci5zZXRMb2NhbGUoJ3dhZ3RhaWxfY3VzdG9tX2xvY2FsZScpO1xuLy8gQ29tcGFyZSB0d28gZGF0ZSBvYmplY3RzLiBJZ25vcmUgbWludXRlcyBhbmQgc2Vjb25kcy5cbmZ1bmN0aW9uIGRhdGVFcXVhbCh4LCB5KSB7XG4gICAgcmV0dXJuICh4LmdldERhdGUoKSA9PT0geS5nZXREYXRlKCkgJiZcbiAgICAgICAgeC5nZXRNb250aCgpID09PSB5LmdldE1vbnRoKCkgJiZcbiAgICAgICAgeC5nZXRZZWFyKCkgPT09IHkuZ2V0WWVhcigpKTtcbn1cbndpbmRvdy5kYXRlRXF1YWwgPSBkYXRlRXF1YWw7XG4vKlxuUmVtb3ZlIHRoZSB4ZHNvZnRfY3VycmVudCBjc3MgY2xhc3MgZnJvbSBtYXJrdXAgdW5sZXNzIHRoZSBzZWxlY3RlZCBkYXRlIGlzIGN1cnJlbnRseSBpbiB2aWV3LlxuS2VlcCB0aGUgbm9ybWFsIGJlaGF2aW91ciBpZiB0aGUgaG9tZSBidXR0b24gaXMgY2xpY2tlZC5cbiAqL1xuZnVuY3Rpb24gaGlkZUN1cnJlbnQoY3VycmVudCwgaW5wdXQpIHtcbiAgICB2YXIgc2VsZWN0ZWQgPSBuZXcgRGF0ZShpbnB1dFswXS52YWx1ZSk7XG4gICAgaWYgKCFkYXRlRXF1YWwoc2VsZWN0ZWQsIGN1cnJlbnQpKSB7XG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKHRoaXMpXG4gICAgICAgICAgICAuZmluZCgnLnhkc29mdF9kYXRlcGlja2VyIC54ZHNvZnRfY3VycmVudDpub3QoLnhkc29mdF90b2RheSknKVxuICAgICAgICAgICAgLnJlbW92ZUNsYXNzKCd4ZHNvZnRfY3VycmVudCcpO1xuICAgIH1cbn1cbndpbmRvdy5oaWRlQ3VycmVudCA9IGhpZGVDdXJyZW50O1xuZnVuY3Rpb24gaW5pdERhdGVDaG9vc2VyKGlkLCBvcHRzKSB7XG4gICAgaWYgKHdpbmRvdy5kYXRlVGltZVBpY2tlclRyYW5zbGF0aW9ucykge1xuICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnIycgKyBpZCkuZGF0ZXRpbWVwaWNrZXIoanF1ZXJ5XzFbXCJkZWZhdWx0XCJdLmV4dGVuZCh7XG4gICAgICAgICAgICBjbG9zZU9uRGF0ZVNlbGVjdDogdHJ1ZSxcbiAgICAgICAgICAgIHRpbWVwaWNrZXI6IGZhbHNlLFxuICAgICAgICAgICAgc2Nyb2xsSW5wdXQ6IGZhbHNlLFxuICAgICAgICAgICAgZm9ybWF0OiAnWS1tLWQnLFxuICAgICAgICAgICAgb25HZW5lcmF0ZTogaGlkZUN1cnJlbnQsXG4gICAgICAgICAgICBvbkNoYW5nZURhdGVUaW1lOiBmdW5jdGlvbiAoXywgJGVsKSB7XG4gICAgICAgICAgICAgICAgJGVsLmdldCgwKS5kaXNwYXRjaEV2ZW50KG5ldyBFdmVudCgnY2hhbmdlJykpO1xuICAgICAgICAgICAgfVxuICAgICAgICB9LCBvcHRzIHx8IHt9KSk7XG4gICAgfVxuICAgIGVsc2Uge1xuICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnIycgKyBpZCkuZGF0ZXRpbWVwaWNrZXIoanF1ZXJ5XzFbXCJkZWZhdWx0XCJdLmV4dGVuZCh7XG4gICAgICAgICAgICB0aW1lcGlja2VyOiBmYWxzZSxcbiAgICAgICAgICAgIHNjcm9sbElucHV0OiBmYWxzZSxcbiAgICAgICAgICAgIGZvcm1hdDogJ1ktbS1kJyxcbiAgICAgICAgICAgIG9uR2VuZXJhdGU6IGhpZGVDdXJyZW50LFxuICAgICAgICAgICAgb25DaGFuZ2VEYXRlVGltZTogZnVuY3Rpb24gKF8sICRlbCkge1xuICAgICAgICAgICAgICAgICRlbC5nZXQoMCkuZGlzcGF0Y2hFdmVudChuZXcgRXZlbnQoJ2NoYW5nZScpKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgfSwgb3B0cyB8fCB7fSkpO1xuICAgIH1cbn1cbndpbmRvdy5pbml0RGF0ZUNob29zZXIgPSBpbml0RGF0ZUNob29zZXI7XG5mdW5jdGlvbiBpbml0VGltZUNob29zZXIoaWQsIG9wdHMpIHtcbiAgICBpZiAod2luZG93LmRhdGVUaW1lUGlja2VyVHJhbnNsYXRpb25zKSB7XG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCcjJyArIGlkKS5kYXRldGltZXBpY2tlcihqcXVlcnlfMVtcImRlZmF1bHRcIl0uZXh0ZW5kKHtcbiAgICAgICAgICAgIGNsb3NlT25EYXRlU2VsZWN0OiB0cnVlLFxuICAgICAgICAgICAgZGF0ZXBpY2tlcjogZmFsc2UsXG4gICAgICAgICAgICBzY3JvbGxJbnB1dDogZmFsc2UsXG4gICAgICAgICAgICBmb3JtYXQ6ICdIOmknLFxuICAgICAgICAgICAgb25DaGFuZ2VEYXRlVGltZTogZnVuY3Rpb24gKF8sICRlbCkge1xuICAgICAgICAgICAgICAgICRlbC5nZXQoMCkuZGlzcGF0Y2hFdmVudChuZXcgRXZlbnQoJ2NoYW5nZScpKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgfSwgb3B0cyB8fCB7fSkpO1xuICAgIH1cbiAgICBlbHNlIHtcbiAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJyMnICsgaWQpLmRhdGV0aW1lcGlja2VyKGpxdWVyeV8xW1wiZGVmYXVsdFwiXS5leHRlbmQoe1xuICAgICAgICAgICAgZGF0ZXBpY2tlcjogZmFsc2UsXG4gICAgICAgICAgICBmb3JtYXQ6ICdIOmknLFxuICAgICAgICAgICAgb25DaGFuZ2VEYXRlVGltZTogZnVuY3Rpb24gKF8sICRlbCkge1xuICAgICAgICAgICAgICAgICRlbC5nZXQoMCkuZGlzcGF0Y2hFdmVudChuZXcgRXZlbnQoJ2NoYW5nZScpKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgfSwgb3B0cyB8fCB7fSkpO1xuICAgIH1cbn1cbndpbmRvdy5pbml0VGltZUNob29zZXIgPSBpbml0VGltZUNob29zZXI7XG5mdW5jdGlvbiBpbml0RGF0ZVRpbWVDaG9vc2VyKGlkLCBvcHRzKSB7XG4gICAgaWYgKHdpbmRvdy5kYXRlVGltZVBpY2tlclRyYW5zbGF0aW9ucykge1xuICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnIycgKyBpZCkuZGF0ZXRpbWVwaWNrZXIoanF1ZXJ5XzFbXCJkZWZhdWx0XCJdLmV4dGVuZCh7XG4gICAgICAgICAgICBjbG9zZU9uRGF0ZVNlbGVjdDogdHJ1ZSxcbiAgICAgICAgICAgIGZvcm1hdDogJ1ktbS1kIEg6aScsXG4gICAgICAgICAgICBzY3JvbGxJbnB1dDogZmFsc2UsXG4gICAgICAgICAgICBvbkdlbmVyYXRlOiBoaWRlQ3VycmVudCxcbiAgICAgICAgICAgIG9uQ2hhbmdlRGF0ZVRpbWU6IGZ1bmN0aW9uIChfLCAkZWwpIHtcbiAgICAgICAgICAgICAgICAkZWwuZ2V0KDApLmRpc3BhdGNoRXZlbnQobmV3IEV2ZW50KCdjaGFuZ2UnKSk7XG4gICAgICAgICAgICB9XG4gICAgICAgIH0sIG9wdHMgfHwge30pKTtcbiAgICB9XG4gICAgZWxzZSB7XG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCcjJyArIGlkKS5kYXRldGltZXBpY2tlcihqcXVlcnlfMVtcImRlZmF1bHRcIl0uZXh0ZW5kKHtcbiAgICAgICAgICAgIGZvcm1hdDogJ1ktbS1kIEg6aScsXG4gICAgICAgICAgICBvbkdlbmVyYXRlOiBoaWRlQ3VycmVudCxcbiAgICAgICAgICAgIG9uQ2hhbmdlRGF0ZVRpbWU6IGZ1bmN0aW9uIChfLCAkZWwpIHtcbiAgICAgICAgICAgICAgICAkZWwuZ2V0KDApLmRpc3BhdGNoRXZlbnQobmV3IEV2ZW50KCdjaGFuZ2UnKSk7XG4gICAgICAgICAgICB9XG4gICAgICAgIH0sIG9wdHMgfHwge30pKTtcbiAgICB9XG59XG53aW5kb3cuaW5pdERhdGVUaW1lQ2hvb3NlciA9IGluaXREYXRlVGltZUNob29zZXI7XG4iXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/date-time-chooser.js\n");

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
/******/ 			"date-time-chooser": 0
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
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["wagtail/admin/static/wagtailadmin/js/vendor"], () => (__webpack_require__("./client/src/entrypoints/admin/date-time-chooser.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;