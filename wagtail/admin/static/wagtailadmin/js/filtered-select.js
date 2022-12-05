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

/***/ "./client/src/entrypoints/admin/filtered-select.js":
/*!*********************************************************!*\
  !*** ./client/src/entrypoints/admin/filtered-select.js ***!
  \*********************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

eval("\n/* A select box component that can be dynamically filtered by the option chosen in another select box.\n\n  <div>\n    <label for=\"id_continent\">Continent</label>\n    <select id=\"id_continent\">\n      <option value=\"\">--------</option>\n      <option value=\"1\">Europe</option>\n      <option value=\"2\">Africa</option>\n      <option value=\"3\">Asia</option>\n    </select>\n  </div>\n  <div>\n    <label for=\"id_country\">Country</label>\n    <select id=\"id_country\" data-widget=\"filtered-select\" data-filter-field=\"id_continent\">\n      <option value=\"\">--------</option>\n      <option value=\"1\" data-filter-value=\"3\">China</option>\n      <option value=\"2\" data-filter-value=\"2\">Egypt</option>\n      <option value=\"3\" data-filter-value=\"1\">France</option>\n      <option value=\"4\" data-filter-value=\"1\">Germany</option>\n      <option value=\"5\" data-filter-value=\"3\">Japan</option>\n      <option value=\"6\" data-filter-value=\"1,3\">Russia</option>\n      <option value=\"7\" data-filter-value=\"2\">South Africa</option>\n      <option value=\"8\" data-filter-value=\"1,3\">Turkey</option>\n    </select>\n  </div>\n*/\nvar __importDefault = (this && this.__importDefault) || function (mod) {\n    return (mod && mod.__esModule) ? mod : { \"default\": mod };\n};\nexports.__esModule = true;\nvar jquery_1 = __importDefault(__webpack_require__(/*! jquery */ \"jquery\"));\n(0, jquery_1[\"default\"])(function () {\n    // eslint-disable-next-line func-names\n    (0, jquery_1[\"default\"])('[data-widget=\"filtered-select\"]').each(function () {\n        var sourceSelect = (0, jquery_1[\"default\"])('#' + this.dataset.filterField);\n        var self = (0, jquery_1[\"default\"])(this);\n        var optionData = [];\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('option', this).each(function () {\n            var filterValue;\n            if ('filterValue' in this.dataset) {\n                filterValue = this.dataset.filterValue.split(',');\n            }\n            else {\n                filterValue = [];\n            }\n            optionData.push({\n                value: this.value,\n                label: this.label,\n                filterValue: filterValue\n            });\n        });\n        function updateFromSource() {\n            var currentValue = self.val();\n            self.empty();\n            var chosenFilter = sourceSelect.val();\n            var filteredValues;\n            if (chosenFilter === '') {\n                /* no filter selected - show all options */\n                filteredValues = optionData;\n            }\n            else {\n                filteredValues = [];\n                for (var i = 0; i < optionData.length; i += 1) {\n                    if (optionData[i].value === '' ||\n                        optionData[i].filterValue.indexOf(chosenFilter) !== -1) {\n                        filteredValues.push(optionData[i]);\n                    }\n                }\n            }\n            var foundValue = false;\n            for (var i = 0; i < filteredValues.length; i += 1) {\n                var option = (0, jquery_1[\"default\"])('<option>');\n                option.attr('value', filteredValues[i].value);\n                if (filteredValues[i].value === currentValue)\n                    foundValue = true;\n                option.text(filteredValues[i].label);\n                self.append(option);\n            }\n            if (foundValue) {\n                self.val(currentValue);\n            }\n            else {\n                self.val('');\n            }\n        }\n        updateFromSource();\n        sourceSelect.change(updateFromSource);\n    });\n});\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL2ZpbHRlcmVkLXNlbGVjdC5qcy5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSIsInNvdXJjZXMiOlsid2VicGFjazovL3dhZ3RhaWwvLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL2ZpbHRlcmVkLXNlbGVjdC5qcz80YmViIl0sInNvdXJjZXNDb250ZW50IjpbIlwidXNlIHN0cmljdFwiO1xuLyogQSBzZWxlY3QgYm94IGNvbXBvbmVudCB0aGF0IGNhbiBiZSBkeW5hbWljYWxseSBmaWx0ZXJlZCBieSB0aGUgb3B0aW9uIGNob3NlbiBpbiBhbm90aGVyIHNlbGVjdCBib3guXG5cbiAgPGRpdj5cbiAgICA8bGFiZWwgZm9yPVwiaWRfY29udGluZW50XCI+Q29udGluZW50PC9sYWJlbD5cbiAgICA8c2VsZWN0IGlkPVwiaWRfY29udGluZW50XCI+XG4gICAgICA8b3B0aW9uIHZhbHVlPVwiXCI+LS0tLS0tLS08L29wdGlvbj5cbiAgICAgIDxvcHRpb24gdmFsdWU9XCIxXCI+RXVyb3BlPC9vcHRpb24+XG4gICAgICA8b3B0aW9uIHZhbHVlPVwiMlwiPkFmcmljYTwvb3B0aW9uPlxuICAgICAgPG9wdGlvbiB2YWx1ZT1cIjNcIj5Bc2lhPC9vcHRpb24+XG4gICAgPC9zZWxlY3Q+XG4gIDwvZGl2PlxuICA8ZGl2PlxuICAgIDxsYWJlbCBmb3I9XCJpZF9jb3VudHJ5XCI+Q291bnRyeTwvbGFiZWw+XG4gICAgPHNlbGVjdCBpZD1cImlkX2NvdW50cnlcIiBkYXRhLXdpZGdldD1cImZpbHRlcmVkLXNlbGVjdFwiIGRhdGEtZmlsdGVyLWZpZWxkPVwiaWRfY29udGluZW50XCI+XG4gICAgICA8b3B0aW9uIHZhbHVlPVwiXCI+LS0tLS0tLS08L29wdGlvbj5cbiAgICAgIDxvcHRpb24gdmFsdWU9XCIxXCIgZGF0YS1maWx0ZXItdmFsdWU9XCIzXCI+Q2hpbmE8L29wdGlvbj5cbiAgICAgIDxvcHRpb24gdmFsdWU9XCIyXCIgZGF0YS1maWx0ZXItdmFsdWU9XCIyXCI+RWd5cHQ8L29wdGlvbj5cbiAgICAgIDxvcHRpb24gdmFsdWU9XCIzXCIgZGF0YS1maWx0ZXItdmFsdWU9XCIxXCI+RnJhbmNlPC9vcHRpb24+XG4gICAgICA8b3B0aW9uIHZhbHVlPVwiNFwiIGRhdGEtZmlsdGVyLXZhbHVlPVwiMVwiPkdlcm1hbnk8L29wdGlvbj5cbiAgICAgIDxvcHRpb24gdmFsdWU9XCI1XCIgZGF0YS1maWx0ZXItdmFsdWU9XCIzXCI+SmFwYW48L29wdGlvbj5cbiAgICAgIDxvcHRpb24gdmFsdWU9XCI2XCIgZGF0YS1maWx0ZXItdmFsdWU9XCIxLDNcIj5SdXNzaWE8L29wdGlvbj5cbiAgICAgIDxvcHRpb24gdmFsdWU9XCI3XCIgZGF0YS1maWx0ZXItdmFsdWU9XCIyXCI+U291dGggQWZyaWNhPC9vcHRpb24+XG4gICAgICA8b3B0aW9uIHZhbHVlPVwiOFwiIGRhdGEtZmlsdGVyLXZhbHVlPVwiMSwzXCI+VHVya2V5PC9vcHRpb24+XG4gICAgPC9zZWxlY3Q+XG4gIDwvZGl2PlxuKi9cbnZhciBfX2ltcG9ydERlZmF1bHQgPSAodGhpcyAmJiB0aGlzLl9faW1wb3J0RGVmYXVsdCkgfHwgZnVuY3Rpb24gKG1vZCkge1xuICAgIHJldHVybiAobW9kICYmIG1vZC5fX2VzTW9kdWxlKSA/IG1vZCA6IHsgXCJkZWZhdWx0XCI6IG1vZCB9O1xufTtcbmV4cG9ydHMuX19lc01vZHVsZSA9IHRydWU7XG52YXIganF1ZXJ5XzEgPSBfX2ltcG9ydERlZmF1bHQocmVxdWlyZShcImpxdWVyeVwiKSk7XG4oMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKShmdW5jdGlvbiAoKSB7XG4gICAgLy8gZXNsaW50LWRpc2FibGUtbmV4dC1saW5lIGZ1bmMtbmFtZXNcbiAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnW2RhdGEtd2lkZ2V0PVwiZmlsdGVyZWQtc2VsZWN0XCJdJykuZWFjaChmdW5jdGlvbiAoKSB7XG4gICAgICAgIHZhciBzb3VyY2VTZWxlY3QgPSAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnIycgKyB0aGlzLmRhdGFzZXQuZmlsdGVyRmllbGQpO1xuICAgICAgICB2YXIgc2VsZiA9ICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKHRoaXMpO1xuICAgICAgICB2YXIgb3B0aW9uRGF0YSA9IFtdO1xuICAgICAgICAvLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgZnVuYy1uYW1lc1xuICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnb3B0aW9uJywgdGhpcykuZWFjaChmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICB2YXIgZmlsdGVyVmFsdWU7XG4gICAgICAgICAgICBpZiAoJ2ZpbHRlclZhbHVlJyBpbiB0aGlzLmRhdGFzZXQpIHtcbiAgICAgICAgICAgICAgICBmaWx0ZXJWYWx1ZSA9IHRoaXMuZGF0YXNldC5maWx0ZXJWYWx1ZS5zcGxpdCgnLCcpO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgZWxzZSB7XG4gICAgICAgICAgICAgICAgZmlsdGVyVmFsdWUgPSBbXTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIG9wdGlvbkRhdGEucHVzaCh7XG4gICAgICAgICAgICAgICAgdmFsdWU6IHRoaXMudmFsdWUsXG4gICAgICAgICAgICAgICAgbGFiZWw6IHRoaXMubGFiZWwsXG4gICAgICAgICAgICAgICAgZmlsdGVyVmFsdWU6IGZpbHRlclZhbHVlXG4gICAgICAgICAgICB9KTtcbiAgICAgICAgfSk7XG4gICAgICAgIGZ1bmN0aW9uIHVwZGF0ZUZyb21Tb3VyY2UoKSB7XG4gICAgICAgICAgICB2YXIgY3VycmVudFZhbHVlID0gc2VsZi52YWwoKTtcbiAgICAgICAgICAgIHNlbGYuZW1wdHkoKTtcbiAgICAgICAgICAgIHZhciBjaG9zZW5GaWx0ZXIgPSBzb3VyY2VTZWxlY3QudmFsKCk7XG4gICAgICAgICAgICB2YXIgZmlsdGVyZWRWYWx1ZXM7XG4gICAgICAgICAgICBpZiAoY2hvc2VuRmlsdGVyID09PSAnJykge1xuICAgICAgICAgICAgICAgIC8qIG5vIGZpbHRlciBzZWxlY3RlZCAtIHNob3cgYWxsIG9wdGlvbnMgKi9cbiAgICAgICAgICAgICAgICBmaWx0ZXJlZFZhbHVlcyA9IG9wdGlvbkRhdGE7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgICAgICBmaWx0ZXJlZFZhbHVlcyA9IFtdO1xuICAgICAgICAgICAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgb3B0aW9uRGF0YS5sZW5ndGg7IGkgKz0gMSkge1xuICAgICAgICAgICAgICAgICAgICBpZiAob3B0aW9uRGF0YVtpXS52YWx1ZSA9PT0gJycgfHxcbiAgICAgICAgICAgICAgICAgICAgICAgIG9wdGlvbkRhdGFbaV0uZmlsdGVyVmFsdWUuaW5kZXhPZihjaG9zZW5GaWx0ZXIpICE9PSAtMSkge1xuICAgICAgICAgICAgICAgICAgICAgICAgZmlsdGVyZWRWYWx1ZXMucHVzaChvcHRpb25EYXRhW2ldKTtcbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIHZhciBmb3VuZFZhbHVlID0gZmFsc2U7XG4gICAgICAgICAgICBmb3IgKHZhciBpID0gMDsgaSA8IGZpbHRlcmVkVmFsdWVzLmxlbmd0aDsgaSArPSAxKSB7XG4gICAgICAgICAgICAgICAgdmFyIG9wdGlvbiA9ICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCc8b3B0aW9uPicpO1xuICAgICAgICAgICAgICAgIG9wdGlvbi5hdHRyKCd2YWx1ZScsIGZpbHRlcmVkVmFsdWVzW2ldLnZhbHVlKTtcbiAgICAgICAgICAgICAgICBpZiAoZmlsdGVyZWRWYWx1ZXNbaV0udmFsdWUgPT09IGN1cnJlbnRWYWx1ZSlcbiAgICAgICAgICAgICAgICAgICAgZm91bmRWYWx1ZSA9IHRydWU7XG4gICAgICAgICAgICAgICAgb3B0aW9uLnRleHQoZmlsdGVyZWRWYWx1ZXNbaV0ubGFiZWwpO1xuICAgICAgICAgICAgICAgIHNlbGYuYXBwZW5kKG9wdGlvbik7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBpZiAoZm91bmRWYWx1ZSkge1xuICAgICAgICAgICAgICAgIHNlbGYudmFsKGN1cnJlbnRWYWx1ZSk7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgICAgICBzZWxmLnZhbCgnJyk7XG4gICAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICAgICAgdXBkYXRlRnJvbVNvdXJjZSgpO1xuICAgICAgICBzb3VyY2VTZWxlY3QuY2hhbmdlKHVwZGF0ZUZyb21Tb3VyY2UpO1xuICAgIH0pO1xufSk7XG4iXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/filtered-select.js\n");

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
/******/ 			"filtered-select": 0
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
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["wagtail/admin/static/wagtailadmin/js/vendor"], () => (__webpack_require__("./client/src/entrypoints/admin/filtered-select.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;