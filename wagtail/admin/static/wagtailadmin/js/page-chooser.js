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

/***/ "./client/src/entrypoints/admin/page-chooser.js":
/*!******************************************************!*\
  !*** ./client/src/entrypoints/admin/page-chooser.js ***!
  \******************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

eval("\nvar __extends = (this && this.__extends) || (function () {\n    var extendStatics = function (d, b) {\n        extendStatics = Object.setPrototypeOf ||\n            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||\n            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };\n        return extendStatics(d, b);\n    };\n    return function (d, b) {\n        if (typeof b !== \"function\" && b !== null)\n            throw new TypeError(\"Class extends value \" + String(b) + \" is not a constructor or null\");\n        extendStatics(d, b);\n        function __() { this.constructor = d; }\n        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());\n    };\n})();\nexports.__esModule = true;\nvar ChooserWidget_1 = __webpack_require__(/*! ../../components/ChooserWidget */ \"./client/src/components/ChooserWidget/index.js\");\nvar PageChooser = /** @class */ (function (_super) {\n    __extends(PageChooser, _super);\n    function PageChooser(id, parentId, options) {\n        var _this = this;\n        _this.initialParentId = parentId;\n        _this.options = options;\n        _this = _super.call(this, id) || this;\n        // eslint-disable-next-line no-undef\n        _this.modalOnloadHandlers = PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS;\n        _this.titleStateKey = 'adminTitle';\n        _this.editUrlStateKey = 'editUrl';\n        _this.chosenResponseName = 'pageChosen';\n        return _this;\n    }\n    PageChooser.prototype.getStateFromHTML = function () {\n        var state = _super.prototype.getStateFromHTML.call(this);\n        if (state) {\n            state.parentId = this.initialParentId;\n        }\n        return state;\n    };\n    PageChooser.prototype.getModalUrl = function () {\n        var url = _super.prototype.getModalUrl.call(this);\n        if (this.state && this.state.parentId) {\n            url += this.state.parentId + '/';\n        }\n        return url;\n    };\n    PageChooser.prototype.getModalUrlParams = function () {\n        var urlParams = { page_type: this.options.model_names.join(',') };\n        if (this.options.target_pages) {\n            urlParams.target_pages = this.options.target_pages;\n        }\n        if (this.options.match_subclass) {\n            urlParams.match_subclass = this.options.match_subclass;\n        }\n        if (this.options.can_choose_root) {\n            urlParams.can_choose_root = 'true';\n        }\n        if (this.options.user_perms) {\n            urlParams.user_perms = this.options.user_perms;\n        }\n        return urlParams;\n    };\n    return PageChooser;\n}(ChooserWidget_1.Chooser));\nwindow.PageChooser = PageChooser;\nfunction createPageChooser(id, parentId, options) {\n    /* RemovedInWagtail50Warning */\n    return new PageChooser(id, parentId, options);\n}\nwindow.createPageChooser = createPageChooser;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL3BhZ2UtY2hvb3Nlci5qcy5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSIsInNvdXJjZXMiOlsid2VicGFjazovL3dhZ3RhaWwvLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL3BhZ2UtY2hvb3Nlci5qcz9kYTI3Il0sInNvdXJjZXNDb250ZW50IjpbIlwidXNlIHN0cmljdFwiO1xudmFyIF9fZXh0ZW5kcyA9ICh0aGlzICYmIHRoaXMuX19leHRlbmRzKSB8fCAoZnVuY3Rpb24gKCkge1xuICAgIHZhciBleHRlbmRTdGF0aWNzID0gZnVuY3Rpb24gKGQsIGIpIHtcbiAgICAgICAgZXh0ZW5kU3RhdGljcyA9IE9iamVjdC5zZXRQcm90b3R5cGVPZiB8fFxuICAgICAgICAgICAgKHsgX19wcm90b19fOiBbXSB9IGluc3RhbmNlb2YgQXJyYXkgJiYgZnVuY3Rpb24gKGQsIGIpIHsgZC5fX3Byb3RvX18gPSBiOyB9KSB8fFxuICAgICAgICAgICAgZnVuY3Rpb24gKGQsIGIpIHsgZm9yICh2YXIgcCBpbiBiKSBpZiAoT2JqZWN0LnByb3RvdHlwZS5oYXNPd25Qcm9wZXJ0eS5jYWxsKGIsIHApKSBkW3BdID0gYltwXTsgfTtcbiAgICAgICAgcmV0dXJuIGV4dGVuZFN0YXRpY3MoZCwgYik7XG4gICAgfTtcbiAgICByZXR1cm4gZnVuY3Rpb24gKGQsIGIpIHtcbiAgICAgICAgaWYgKHR5cGVvZiBiICE9PSBcImZ1bmN0aW9uXCIgJiYgYiAhPT0gbnVsbClcbiAgICAgICAgICAgIHRocm93IG5ldyBUeXBlRXJyb3IoXCJDbGFzcyBleHRlbmRzIHZhbHVlIFwiICsgU3RyaW5nKGIpICsgXCIgaXMgbm90IGEgY29uc3RydWN0b3Igb3IgbnVsbFwiKTtcbiAgICAgICAgZXh0ZW5kU3RhdGljcyhkLCBiKTtcbiAgICAgICAgZnVuY3Rpb24gX18oKSB7IHRoaXMuY29uc3RydWN0b3IgPSBkOyB9XG4gICAgICAgIGQucHJvdG90eXBlID0gYiA9PT0gbnVsbCA/IE9iamVjdC5jcmVhdGUoYikgOiAoX18ucHJvdG90eXBlID0gYi5wcm90b3R5cGUsIG5ldyBfXygpKTtcbiAgICB9O1xufSkoKTtcbmV4cG9ydHMuX19lc01vZHVsZSA9IHRydWU7XG52YXIgQ2hvb3NlcldpZGdldF8xID0gcmVxdWlyZShcIi4uLy4uL2NvbXBvbmVudHMvQ2hvb3NlcldpZGdldFwiKTtcbnZhciBQYWdlQ2hvb3NlciA9IC8qKiBAY2xhc3MgKi8gKGZ1bmN0aW9uIChfc3VwZXIpIHtcbiAgICBfX2V4dGVuZHMoUGFnZUNob29zZXIsIF9zdXBlcik7XG4gICAgZnVuY3Rpb24gUGFnZUNob29zZXIoaWQsIHBhcmVudElkLCBvcHRpb25zKSB7XG4gICAgICAgIHZhciBfdGhpcyA9IHRoaXM7XG4gICAgICAgIF90aGlzLmluaXRpYWxQYXJlbnRJZCA9IHBhcmVudElkO1xuICAgICAgICBfdGhpcy5vcHRpb25zID0gb3B0aW9ucztcbiAgICAgICAgX3RoaXMgPSBfc3VwZXIuY2FsbCh0aGlzLCBpZCkgfHwgdGhpcztcbiAgICAgICAgLy8gZXNsaW50LWRpc2FibGUtbmV4dC1saW5lIG5vLXVuZGVmXG4gICAgICAgIF90aGlzLm1vZGFsT25sb2FkSGFuZGxlcnMgPSBQQUdFX0NIT09TRVJfTU9EQUxfT05MT0FEX0hBTkRMRVJTO1xuICAgICAgICBfdGhpcy50aXRsZVN0YXRlS2V5ID0gJ2FkbWluVGl0bGUnO1xuICAgICAgICBfdGhpcy5lZGl0VXJsU3RhdGVLZXkgPSAnZWRpdFVybCc7XG4gICAgICAgIF90aGlzLmNob3NlblJlc3BvbnNlTmFtZSA9ICdwYWdlQ2hvc2VuJztcbiAgICAgICAgcmV0dXJuIF90aGlzO1xuICAgIH1cbiAgICBQYWdlQ2hvb3Nlci5wcm90b3R5cGUuZ2V0U3RhdGVGcm9tSFRNTCA9IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgdmFyIHN0YXRlID0gX3N1cGVyLnByb3RvdHlwZS5nZXRTdGF0ZUZyb21IVE1MLmNhbGwodGhpcyk7XG4gICAgICAgIGlmIChzdGF0ZSkge1xuICAgICAgICAgICAgc3RhdGUucGFyZW50SWQgPSB0aGlzLmluaXRpYWxQYXJlbnRJZDtcbiAgICAgICAgfVxuICAgICAgICByZXR1cm4gc3RhdGU7XG4gICAgfTtcbiAgICBQYWdlQ2hvb3Nlci5wcm90b3R5cGUuZ2V0TW9kYWxVcmwgPSBmdW5jdGlvbiAoKSB7XG4gICAgICAgIHZhciB1cmwgPSBfc3VwZXIucHJvdG90eXBlLmdldE1vZGFsVXJsLmNhbGwodGhpcyk7XG4gICAgICAgIGlmICh0aGlzLnN0YXRlICYmIHRoaXMuc3RhdGUucGFyZW50SWQpIHtcbiAgICAgICAgICAgIHVybCArPSB0aGlzLnN0YXRlLnBhcmVudElkICsgJy8nO1xuICAgICAgICB9XG4gICAgICAgIHJldHVybiB1cmw7XG4gICAgfTtcbiAgICBQYWdlQ2hvb3Nlci5wcm90b3R5cGUuZ2V0TW9kYWxVcmxQYXJhbXMgPSBmdW5jdGlvbiAoKSB7XG4gICAgICAgIHZhciB1cmxQYXJhbXMgPSB7IHBhZ2VfdHlwZTogdGhpcy5vcHRpb25zLm1vZGVsX25hbWVzLmpvaW4oJywnKSB9O1xuICAgICAgICBpZiAodGhpcy5vcHRpb25zLnRhcmdldF9wYWdlcykge1xuICAgICAgICAgICAgdXJsUGFyYW1zLnRhcmdldF9wYWdlcyA9IHRoaXMub3B0aW9ucy50YXJnZXRfcGFnZXM7XG4gICAgICAgIH1cbiAgICAgICAgaWYgKHRoaXMub3B0aW9ucy5tYXRjaF9zdWJjbGFzcykge1xuICAgICAgICAgICAgdXJsUGFyYW1zLm1hdGNoX3N1YmNsYXNzID0gdGhpcy5vcHRpb25zLm1hdGNoX3N1YmNsYXNzO1xuICAgICAgICB9XG4gICAgICAgIGlmICh0aGlzLm9wdGlvbnMuY2FuX2Nob29zZV9yb290KSB7XG4gICAgICAgICAgICB1cmxQYXJhbXMuY2FuX2Nob29zZV9yb290ID0gJ3RydWUnO1xuICAgICAgICB9XG4gICAgICAgIGlmICh0aGlzLm9wdGlvbnMudXNlcl9wZXJtcykge1xuICAgICAgICAgICAgdXJsUGFyYW1zLnVzZXJfcGVybXMgPSB0aGlzLm9wdGlvbnMudXNlcl9wZXJtcztcbiAgICAgICAgfVxuICAgICAgICByZXR1cm4gdXJsUGFyYW1zO1xuICAgIH07XG4gICAgcmV0dXJuIFBhZ2VDaG9vc2VyO1xufShDaG9vc2VyV2lkZ2V0XzEuQ2hvb3NlcikpO1xud2luZG93LlBhZ2VDaG9vc2VyID0gUGFnZUNob29zZXI7XG5mdW5jdGlvbiBjcmVhdGVQYWdlQ2hvb3NlcihpZCwgcGFyZW50SWQsIG9wdGlvbnMpIHtcbiAgICAvKiBSZW1vdmVkSW5XYWd0YWlsNTBXYXJuaW5nICovXG4gICAgcmV0dXJuIG5ldyBQYWdlQ2hvb3NlcihpZCwgcGFyZW50SWQsIG9wdGlvbnMpO1xufVxud2luZG93LmNyZWF0ZVBhZ2VDaG9vc2VyID0gY3JlYXRlUGFnZUNob29zZXI7XG4iXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/page-chooser.js\n");

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
/******/ 			"page-chooser": 0
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
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["wagtail/admin/static/wagtailadmin/js/vendor"], () => (__webpack_require__("./client/src/entrypoints/admin/page-chooser.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;