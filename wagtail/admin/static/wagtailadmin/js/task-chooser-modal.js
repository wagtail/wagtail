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

/***/ "./client/src/entrypoints/admin/task-chooser-modal.js":
/*!************************************************************!*\
  !*** ./client/src/entrypoints/admin/task-chooser-modal.js ***!
  \************************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

eval("\nvar __importDefault = (this && this.__importDefault) || function (mod) {\n    return (mod && mod.__esModule) ? mod : { \"default\": mod };\n};\nexports.__esModule = true;\nvar jquery_1 = __importDefault(__webpack_require__(/*! jquery */ \"jquery\"));\nvar tabs_1 = __webpack_require__(/*! ../../includes/tabs */ \"./client/src/includes/tabs.js\");\nvar chooserModal_1 = __webpack_require__(/*! ../../includes/chooserModal */ \"./client/src/includes/chooserModal.js\");\nvar ajaxifyTaskCreateTab = function (modal) {\n    (0, jquery_1[\"default\"])('#tab-new a.task-type-choice, #tab-new a.choose-different-task-type', modal.body).on('click', function onClickNew() {\n        modal.loadUrl(this.href);\n        return false;\n    });\n    // eslint-disable-next-line func-names\n    (0, jquery_1[\"default\"])('form.task-create', modal.body).on('submit', function () {\n        (0, chooserModal_1.submitCreationForm)(modal, this, { errorContainerSelector: '#tab-new' });\n        return false;\n    });\n};\nvar TASK_CHOOSER_MODAL_ONLOAD_HANDLERS = {\n    chooser: function (modal, jsonData) {\n        function ajaxifyLinks(context) {\n            (0, jquery_1[\"default\"])('a.task-choice', context)\n                // eslint-disable-next-line func-names\n                .on('click', function () {\n                modal.loadUrl(this.href);\n                return false;\n            });\n            // eslint-disable-next-line func-names\n            (0, jquery_1[\"default\"])('.pagination a', context).on('click', function () {\n                // eslint-disable-next-line @typescript-eslint/no-use-before-define\n                searchController.fetchResults(this.href);\n                return false;\n            });\n            // Reinitialize tabs to hook up tab event listeners in the modal\n            (0, tabs_1.initTabs)();\n        }\n        var searchController = new chooserModal_1.SearchController({\n            form: (0, jquery_1[\"default\"])('form.task-search', modal.body),\n            containerElement: modal.body,\n            resultsContainerSelector: '#search-results',\n            onLoadResults: function (context) {\n                ajaxifyLinks(context);\n            },\n            inputDelay: 50\n        });\n        searchController.attachSearchInput('#id_q');\n        searchController.attachSearchFilter('#id_task_type');\n        ajaxifyLinks(modal.body);\n        ajaxifyTaskCreateTab(modal, jsonData);\n    },\n    task_chosen: function (modal, jsonData) {\n        modal.respond('taskChosen', jsonData.result);\n        modal.close();\n    },\n    reshow_create_tab: function (modal, jsonData) {\n        (0, jquery_1[\"default\"])('#tab-new', modal.body).html(jsonData.htmlFragment);\n        ajaxifyTaskCreateTab(modal, jsonData);\n    }\n};\nwindow.TASK_CHOOSER_MODAL_ONLOAD_HANDLERS = TASK_CHOOSER_MODAL_ONLOAD_HANDLERS;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL3Rhc2stY2hvb3Nlci1tb2RhbC5qcy5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSIsInNvdXJjZXMiOlsid2VicGFjazovL3dhZ3RhaWwvLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL3Rhc2stY2hvb3Nlci1tb2RhbC5qcz83MDhhIl0sInNvdXJjZXNDb250ZW50IjpbIlwidXNlIHN0cmljdFwiO1xudmFyIF9faW1wb3J0RGVmYXVsdCA9ICh0aGlzICYmIHRoaXMuX19pbXBvcnREZWZhdWx0KSB8fCBmdW5jdGlvbiAobW9kKSB7XG4gICAgcmV0dXJuIChtb2QgJiYgbW9kLl9fZXNNb2R1bGUpID8gbW9kIDogeyBcImRlZmF1bHRcIjogbW9kIH07XG59O1xuZXhwb3J0cy5fX2VzTW9kdWxlID0gdHJ1ZTtcbnZhciBqcXVlcnlfMSA9IF9faW1wb3J0RGVmYXVsdChyZXF1aXJlKFwianF1ZXJ5XCIpKTtcbnZhciB0YWJzXzEgPSByZXF1aXJlKFwiLi4vLi4vaW5jbHVkZXMvdGFic1wiKTtcbnZhciBjaG9vc2VyTW9kYWxfMSA9IHJlcXVpcmUoXCIuLi8uLi9pbmNsdWRlcy9jaG9vc2VyTW9kYWxcIik7XG52YXIgYWpheGlmeVRhc2tDcmVhdGVUYWIgPSBmdW5jdGlvbiAobW9kYWwpIHtcbiAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnI3RhYi1uZXcgYS50YXNrLXR5cGUtY2hvaWNlLCAjdGFiLW5ldyBhLmNob29zZS1kaWZmZXJlbnQtdGFzay10eXBlJywgbW9kYWwuYm9keSkub24oJ2NsaWNrJywgZnVuY3Rpb24gb25DbGlja05ldygpIHtcbiAgICAgICAgbW9kYWwubG9hZFVybCh0aGlzLmhyZWYpO1xuICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgfSk7XG4gICAgLy8gZXNsaW50LWRpc2FibGUtbmV4dC1saW5lIGZ1bmMtbmFtZXNcbiAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnZm9ybS50YXNrLWNyZWF0ZScsIG1vZGFsLmJvZHkpLm9uKCdzdWJtaXQnLCBmdW5jdGlvbiAoKSB7XG4gICAgICAgICgwLCBjaG9vc2VyTW9kYWxfMS5zdWJtaXRDcmVhdGlvbkZvcm0pKG1vZGFsLCB0aGlzLCB7IGVycm9yQ29udGFpbmVyU2VsZWN0b3I6ICcjdGFiLW5ldycgfSk7XG4gICAgICAgIHJldHVybiBmYWxzZTtcbiAgICB9KTtcbn07XG52YXIgVEFTS19DSE9PU0VSX01PREFMX09OTE9BRF9IQU5ETEVSUyA9IHtcbiAgICBjaG9vc2VyOiBmdW5jdGlvbiAobW9kYWwsIGpzb25EYXRhKSB7XG4gICAgICAgIGZ1bmN0aW9uIGFqYXhpZnlMaW5rcyhjb250ZXh0KSB7XG4gICAgICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnYS50YXNrLWNob2ljZScsIGNvbnRleHQpXG4gICAgICAgICAgICAgICAgLy8gZXNsaW50LWRpc2FibGUtbmV4dC1saW5lIGZ1bmMtbmFtZXNcbiAgICAgICAgICAgICAgICAub24oJ2NsaWNrJywgZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgICAgIG1vZGFsLmxvYWRVcmwodGhpcy5ocmVmKTtcbiAgICAgICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgICAgICB9KTtcbiAgICAgICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnLnBhZ2luYXRpb24gYScsIGNvbnRleHQpLm9uKCdjbGljaycsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgICAgICAvLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgQHR5cGVzY3JpcHQtZXNsaW50L25vLXVzZS1iZWZvcmUtZGVmaW5lXG4gICAgICAgICAgICAgICAgc2VhcmNoQ29udHJvbGxlci5mZXRjaFJlc3VsdHModGhpcy5ocmVmKTtcbiAgICAgICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgICAgICB9KTtcbiAgICAgICAgICAgIC8vIFJlaW5pdGlhbGl6ZSB0YWJzIHRvIGhvb2sgdXAgdGFiIGV2ZW50IGxpc3RlbmVycyBpbiB0aGUgbW9kYWxcbiAgICAgICAgICAgICgwLCB0YWJzXzEuaW5pdFRhYnMpKCk7XG4gICAgICAgIH1cbiAgICAgICAgdmFyIHNlYXJjaENvbnRyb2xsZXIgPSBuZXcgY2hvb3Nlck1vZGFsXzEuU2VhcmNoQ29udHJvbGxlcih7XG4gICAgICAgICAgICBmb3JtOiAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnZm9ybS50YXNrLXNlYXJjaCcsIG1vZGFsLmJvZHkpLFxuICAgICAgICAgICAgY29udGFpbmVyRWxlbWVudDogbW9kYWwuYm9keSxcbiAgICAgICAgICAgIHJlc3VsdHNDb250YWluZXJTZWxlY3RvcjogJyNzZWFyY2gtcmVzdWx0cycsXG4gICAgICAgICAgICBvbkxvYWRSZXN1bHRzOiBmdW5jdGlvbiAoY29udGV4dCkge1xuICAgICAgICAgICAgICAgIGFqYXhpZnlMaW5rcyhjb250ZXh0KTtcbiAgICAgICAgICAgIH0sXG4gICAgICAgICAgICBpbnB1dERlbGF5OiA1MFxuICAgICAgICB9KTtcbiAgICAgICAgc2VhcmNoQ29udHJvbGxlci5hdHRhY2hTZWFyY2hJbnB1dCgnI2lkX3EnKTtcbiAgICAgICAgc2VhcmNoQ29udHJvbGxlci5hdHRhY2hTZWFyY2hGaWx0ZXIoJyNpZF90YXNrX3R5cGUnKTtcbiAgICAgICAgYWpheGlmeUxpbmtzKG1vZGFsLmJvZHkpO1xuICAgICAgICBhamF4aWZ5VGFza0NyZWF0ZVRhYihtb2RhbCwganNvbkRhdGEpO1xuICAgIH0sXG4gICAgdGFza19jaG9zZW46IGZ1bmN0aW9uIChtb2RhbCwganNvbkRhdGEpIHtcbiAgICAgICAgbW9kYWwucmVzcG9uZCgndGFza0Nob3NlbicsIGpzb25EYXRhLnJlc3VsdCk7XG4gICAgICAgIG1vZGFsLmNsb3NlKCk7XG4gICAgfSxcbiAgICByZXNob3dfY3JlYXRlX3RhYjogZnVuY3Rpb24gKG1vZGFsLCBqc29uRGF0YSkge1xuICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnI3RhYi1uZXcnLCBtb2RhbC5ib2R5KS5odG1sKGpzb25EYXRhLmh0bWxGcmFnbWVudCk7XG4gICAgICAgIGFqYXhpZnlUYXNrQ3JlYXRlVGFiKG1vZGFsLCBqc29uRGF0YSk7XG4gICAgfVxufTtcbndpbmRvdy5UQVNLX0NIT09TRVJfTU9EQUxfT05MT0FEX0hBTkRMRVJTID0gVEFTS19DSE9PU0VSX01PREFMX09OTE9BRF9IQU5ETEVSUztcbiJdLCJuYW1lcyI6W10sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/task-chooser-modal.js\n");

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
/******/ 			"task-chooser-modal": 0
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
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["wagtail/admin/static/wagtailadmin/js/vendor"], () => (__webpack_require__("./client/src/entrypoints/admin/task-chooser-modal.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;