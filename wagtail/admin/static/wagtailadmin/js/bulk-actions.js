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

/***/ "./client/src/entrypoints/admin/bulk-actions.js":
/*!******************************************************!*\
  !*** ./client/src/entrypoints/admin/bulk-actions.js ***!
  \******************************************************/
/***/ ((__unused_webpack_module, exports, __webpack_require__) => {

eval("\nexports.__esModule = true;\nvar bulk_actions_1 = __webpack_require__(/*! ../../includes/bulk-actions */ \"./client/src/includes/bulk-actions.js\");\ndocument.addEventListener('DOMContentLoaded', bulk_actions_1.addBulkActionListeners);\nif (window.headerSearch) {\n    var termInput = document.querySelector(window.headerSearch.termInput);\n    if (termInput) {\n        termInput.addEventListener('search-success', bulk_actions_1.rebindBulkActionsEventListeners);\n    }\n}\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL2J1bGstYWN0aW9ucy5qcy5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSIsInNvdXJjZXMiOlsid2VicGFjazovL3dhZ3RhaWwvLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL2J1bGstYWN0aW9ucy5qcz84Y2Y3Il0sInNvdXJjZXNDb250ZW50IjpbIlwidXNlIHN0cmljdFwiO1xuZXhwb3J0cy5fX2VzTW9kdWxlID0gdHJ1ZTtcbnZhciBidWxrX2FjdGlvbnNfMSA9IHJlcXVpcmUoXCIuLi8uLi9pbmNsdWRlcy9idWxrLWFjdGlvbnNcIik7XG5kb2N1bWVudC5hZGRFdmVudExpc3RlbmVyKCdET01Db250ZW50TG9hZGVkJywgYnVsa19hY3Rpb25zXzEuYWRkQnVsa0FjdGlvbkxpc3RlbmVycyk7XG5pZiAod2luZG93LmhlYWRlclNlYXJjaCkge1xuICAgIHZhciB0ZXJtSW5wdXQgPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKHdpbmRvdy5oZWFkZXJTZWFyY2gudGVybUlucHV0KTtcbiAgICBpZiAodGVybUlucHV0KSB7XG4gICAgICAgIHRlcm1JbnB1dC5hZGRFdmVudExpc3RlbmVyKCdzZWFyY2gtc3VjY2VzcycsIGJ1bGtfYWN0aW9uc18xLnJlYmluZEJ1bGtBY3Rpb25zRXZlbnRMaXN0ZW5lcnMpO1xuICAgIH1cbn1cbiJdLCJuYW1lcyI6W10sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/bulk-actions.js\n");

/***/ }),

/***/ "./client/src/includes/bulk-actions.js":
/*!*********************************************!*\
  !*** ./client/src/includes/bulk-actions.js ***!
  \*********************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

eval("\n/* global wagtailConfig */\nvar __read = (this && this.__read) || function (o, n) {\n    var m = typeof Symbol === \"function\" && o[Symbol.iterator];\n    if (!m) return o;\n    var i = m.call(o), r, ar = [], e;\n    try {\n        while ((n === void 0 || n-- > 0) && !(r = i.next()).done) ar.push(r.value);\n    }\n    catch (error) { e = { error: error }; }\n    finally {\n        try {\n            if (r && !r.done && (m = i[\"return\"])) m.call(i);\n        }\n        finally { if (e) throw e.error; }\n    }\n    return ar;\n};\nvar __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {\n    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {\n        if (ar || !(i in from)) {\n            if (!ar) ar = Array.prototype.slice.call(from, 0, i);\n            ar[i] = from[i];\n        }\n    }\n    return to.concat(ar || Array.prototype.slice.call(from));\n};\nexports.__esModule = true;\nexports.rebindBulkActionsEventListeners = exports.addBulkActionListeners = void 0;\nvar range_1 = __webpack_require__(/*! ../utils/range */ \"./client/src/utils/range.ts\");\nvar BULK_ACTION_PAGE_CHECKBOX_INPUT = '[data-bulk-action-checkbox]';\nvar BULK_ACTION_SELECT_ALL_CHECKBOX = '[data-bulk-action-select-all-checkbox]';\nvar BULK_ACTIONS_CHECKBOX_PARENT = '[data-bulk-action-parent-id]';\nvar BULK_ACTION_FOOTER = '[data-bulk-action-footer]';\nvar BULK_ACTION_NUM_OBJECTS = '[data-bulk-action-num-objects]';\nvar BULK_ACTION_NUM_OBJECTS_IN_LISTING = '[data-bulk-action-num-objects-in-listing]';\nvar MORE_ACTIONS_DROPDOWN_BUTTON_SELECTOR = '.actions [data-dropdown]';\nvar checkedState = {};\n/**\n * Toggles the 'more' dropdown button in listing pages.\n * @param {boolean} show - Determines if the button should be shown or not.\n */\nfunction toggleMoreActionsDropdownBtn(show) {\n    var moreActionsDropdown = document.querySelector(MORE_ACTIONS_DROPDOWN_BUTTON_SELECTOR);\n    if (moreActionsDropdown !== null) {\n        if (show === true) {\n            moreActionsDropdown.classList.remove('hidden');\n        }\n        else {\n            moreActionsDropdown.classList.add('hidden');\n        }\n    }\n}\n/**\n * Utility function to get the appropriate string for display in action bar\n */\nfunction getStringForListing(key) {\n    if (wagtailConfig.STRINGS.BULK_ACTIONS[wagtailConfig.BULK_ACTION_ITEM_TYPE]) {\n        return wagtailConfig.STRINGS.BULK_ACTIONS[wagtailConfig.BULK_ACTION_ITEM_TYPE][key];\n    }\n    return wagtailConfig.STRINGS.BULK_ACTIONS.ITEM[key];\n}\n/**\n * Event listener for the `Select All` checkbox\n */\nfunction onSelectAllChange(e) {\n    document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach(function (el) {\n        el.checked = e.target.checked; // eslint-disable-line no-param-reassign\n    });\n    var changeEvent = new Event('change');\n    document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach(function (el) {\n        if (el.checked !== e.target.checked) {\n            // eslint-disable-next-line no-param-reassign\n            el.checked = e.target.checked;\n            if (e.target.checked) {\n                el.dispatchEvent(changeEvent);\n            }\n            else {\n                el.classList.remove('show');\n            }\n        }\n    });\n    if (!e.target.checked) {\n        toggleMoreActionsDropdownBtn(true);\n        // when deselecting all checkbox, simply hide the footer for smooth transition\n        checkedState.checkedObjects.clear();\n        document.querySelector(BULK_ACTION_FOOTER).classList.add('hidden');\n    }\n    else {\n        toggleMoreActionsDropdownBtn(false);\n    }\n}\n/**\n * Event listener for clicking individual checkbox and checking if shift key is pressed\n *\n * @param {Event} event\n */\nfunction onClickIndividualCheckbox(event) {\n    if (event.shiftKey && checkedState.prevCheckedObject) {\n        var individualCheckboxList_1 = __spreadArray([], __read(document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT)), false);\n        var prevCheckedObjectIndex_1 = individualCheckboxList_1.findIndex(function (el) { return el.dataset.objectId === checkedState.prevCheckedObject; });\n        var shiftClickedObjectIndex = individualCheckboxList_1.findIndex(function (el) { return el.dataset.objectId === event.target.dataset.objectId; });\n        var startingIndex = (prevCheckedObjectIndex_1 > shiftClickedObjectIndex\n            ? shiftClickedObjectIndex\n            : prevCheckedObjectIndex_1) + 1;\n        var endingIndex = prevCheckedObjectIndex_1 <= shiftClickedObjectIndex\n            ? shiftClickedObjectIndex\n            : prevCheckedObjectIndex_1;\n        (0, range_1.range)(startingIndex, endingIndex).forEach(function (i) {\n            var changeEvent = new Event('change');\n            individualCheckboxList_1[i].checked =\n                individualCheckboxList_1[prevCheckedObjectIndex_1].checked;\n            individualCheckboxList_1[i].dispatchEvent(changeEvent);\n        });\n        checkedState.prevCheckedObject = event.target.dataset.objectId;\n    }\n}\n/**\n * Event listener for individual checkbox\n */\nfunction onSelectIndividualCheckbox(e) {\n    if (checkedState.selectAllInListing)\n        checkedState.selectAllInListing = false;\n    var prevLength = checkedState.checkedObjects.size;\n    if (e.target.checked) {\n        checkedState.checkedObjects.add(e.target.dataset.objectId);\n    }\n    else {\n        /* unchecks `Select all` checkbox as soon as one page is unchecked */\n        document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach(function (el) {\n            el.checked = false; // eslint-disable-line no-param-reassign\n        });\n        checkedState.checkedObjects[\"delete\"](e.target.dataset.objectId);\n    }\n    var numCheckedObjects = checkedState.checkedObjects.size;\n    if (numCheckedObjects === 0) {\n        /* when all checkboxes are unchecked */\n        toggleMoreActionsDropdownBtn(true);\n        document.querySelector(BULK_ACTION_FOOTER).classList.add('hidden');\n        document\n            .querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT)\n            .forEach(function (el) { return el.classList.remove('show'); });\n    }\n    else if (numCheckedObjects === 1 && prevLength === 0) {\n        /* when 1 checkbox is checked for the first time */\n        toggleMoreActionsDropdownBtn(false);\n        document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach(function (el) {\n            el.classList.add('show');\n        });\n        document.querySelector(BULK_ACTION_FOOTER).classList.remove('hidden');\n    }\n    if (numCheckedObjects === checkedState.numObjects) {\n        /* when all checkboxes in the page are checked */\n        document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach(function (el) {\n            el.checked = true; // eslint-disable-line no-param-reassign\n        });\n        if (checkedState.shouldShowAllInListingText) {\n            document\n                .querySelector(BULK_ACTION_NUM_OBJECTS_IN_LISTING)\n                .classList.remove('u-hidden');\n        }\n    }\n    else if (checkedState.shouldShowAllInListingText) {\n        document\n            .querySelector(BULK_ACTION_NUM_OBJECTS_IN_LISTING)\n            .classList.add('u-hidden');\n    }\n    if (numCheckedObjects > 0) {\n        /* Update text on number of pages */\n        var numObjectsSelected = '';\n        if (numCheckedObjects === 1) {\n            numObjectsSelected = getStringForListing('SINGULAR');\n        }\n        else if (numCheckedObjects === checkedState.numObjects) {\n            numObjectsSelected = getStringForListing('ALL').replace('%(objects)s', numCheckedObjects);\n        }\n        else {\n            numObjectsSelected = getStringForListing('PLURAL').replace('%(objects)s', numCheckedObjects);\n        }\n        document.querySelector(BULK_ACTION_NUM_OBJECTS).textContent =\n            numObjectsSelected;\n    }\n    // Updating previously checked object\n    checkedState.prevCheckedObject = e.target.dataset.objectId;\n}\n/**\n * Event listener to select all objects in listing\n */\nfunction onClickSelectAllInListing(e) {\n    e.preventDefault();\n    checkedState.selectAllInListing = true;\n    document.querySelector(BULK_ACTION_NUM_OBJECTS).textContent = \"\".concat(getStringForListing('ALL_IN_LISTING'), \".\");\n    document\n        .querySelector(BULK_ACTION_NUM_OBJECTS_IN_LISTING)\n        .classList.add('u-hidden');\n}\n/**\n * Event listener for bulk actions which appends selected ids to the corresponding action url\n */\nfunction onClickActionButton(e) {\n    e.preventDefault();\n    var url = e.target.getAttribute('href');\n    var urlParams = new URLSearchParams(window.location.search);\n    if (checkedState.selectAllInListing) {\n        urlParams.append('id', 'all');\n        var parentElement = document.querySelector(BULK_ACTIONS_CHECKBOX_PARENT);\n        if (parentElement) {\n            var parentPageId = parentElement.dataset.bulkActionParentId;\n            urlParams.append('childOf', parentPageId);\n        }\n    }\n    else {\n        checkedState.checkedObjects.forEach(function (objectId) {\n            urlParams.append('id', objectId);\n        });\n    }\n    window.location.href = \"\".concat(url, \"&\").concat(urlParams.toString());\n}\n/**\n * Adds all event listeners\n */\nfunction addBulkActionListeners() {\n    checkedState = {\n        checkedObjects: new Set(),\n        numObjects: 0,\n        selectAllInListing: false,\n        shouldShowAllInListingText: true,\n        prevCheckedObject: null\n    };\n    var changeEvent = new Event('change');\n    document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach(function (el) {\n        checkedState.numObjects += 1;\n        el.addEventListener('change', onSelectIndividualCheckbox);\n        el.addEventListener('click', onClickIndividualCheckbox);\n    });\n    document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach(function (el) {\n        el.addEventListener('change', onSelectAllChange);\n    });\n    document\n        .querySelectorAll(\"\".concat(BULK_ACTION_FOOTER, \" .bulk-action-btn\"))\n        .forEach(function (elem) { return elem.addEventListener('click', onClickActionButton); });\n    var selectAllInListingText = document.querySelector(BULK_ACTION_NUM_OBJECTS_IN_LISTING);\n    if (selectAllInListingText)\n        selectAllInListingText.addEventListener('click', onClickSelectAllInListing);\n    else\n        checkedState.shouldShowAllInListingText = false;\n    document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach(function (el) {\n        if (el.checked) {\n            el.dispatchEvent(changeEvent);\n        }\n    });\n}\nexports.addBulkActionListeners = addBulkActionListeners;\nfunction rebindBulkActionsEventListeners() {\n    // when deselecting all checkbox, simply hide the footer for smooth transition\n    document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach(function (el) {\n        el.checked = false; // eslint-disable-line no-param-reassign\n    });\n    document.querySelector(BULK_ACTION_FOOTER).classList.add('hidden');\n    document.querySelectorAll(BULK_ACTION_SELECT_ALL_CHECKBOX).forEach(function (el) {\n        // remove already attached event listener first\n        el.removeEventListener('change', onSelectAllChange);\n        el.addEventListener('change', onSelectAllChange);\n    });\n    checkedState.checkedObjects.clear();\n    checkedState.numObjects = 0;\n    document.querySelectorAll(BULK_ACTION_PAGE_CHECKBOX_INPUT).forEach(function (el) {\n        checkedState.numObjects += 1;\n        el.addEventListener('change', onSelectIndividualCheckbox);\n    });\n}\nexports.rebindBulkActionsEventListeners = rebindBulkActionsEventListeners;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2luY2x1ZGVzL2J1bGstYWN0aW9ucy5qcy5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vd2FndGFpbC8uL2NsaWVudC9zcmMvaW5jbHVkZXMvYnVsay1hY3Rpb25zLmpzPzljYzciXSwic291cmNlc0NvbnRlbnQiOlsiXCJ1c2Ugc3RyaWN0XCI7XG4vKiBnbG9iYWwgd2FndGFpbENvbmZpZyAqL1xudmFyIF9fcmVhZCA9ICh0aGlzICYmIHRoaXMuX19yZWFkKSB8fCBmdW5jdGlvbiAobywgbikge1xuICAgIHZhciBtID0gdHlwZW9mIFN5bWJvbCA9PT0gXCJmdW5jdGlvblwiICYmIG9bU3ltYm9sLml0ZXJhdG9yXTtcbiAgICBpZiAoIW0pIHJldHVybiBvO1xuICAgIHZhciBpID0gbS5jYWxsKG8pLCByLCBhciA9IFtdLCBlO1xuICAgIHRyeSB7XG4gICAgICAgIHdoaWxlICgobiA9PT0gdm9pZCAwIHx8IG4tLSA+IDApICYmICEociA9IGkubmV4dCgpKS5kb25lKSBhci5wdXNoKHIudmFsdWUpO1xuICAgIH1cbiAgICBjYXRjaCAoZXJyb3IpIHsgZSA9IHsgZXJyb3I6IGVycm9yIH07IH1cbiAgICBmaW5hbGx5IHtcbiAgICAgICAgdHJ5IHtcbiAgICAgICAgICAgIGlmIChyICYmICFyLmRvbmUgJiYgKG0gPSBpW1wicmV0dXJuXCJdKSkgbS5jYWxsKGkpO1xuICAgICAgICB9XG4gICAgICAgIGZpbmFsbHkgeyBpZiAoZSkgdGhyb3cgZS5lcnJvcjsgfVxuICAgIH1cbiAgICByZXR1cm4gYXI7XG59O1xudmFyIF9fc3ByZWFkQXJyYXkgPSAodGhpcyAmJiB0aGlzLl9fc3ByZWFkQXJyYXkpIHx8IGZ1bmN0aW9uICh0bywgZnJvbSwgcGFjaykge1xuICAgIGlmIChwYWNrIHx8IGFyZ3VtZW50cy5sZW5ndGggPT09IDIpIGZvciAodmFyIGkgPSAwLCBsID0gZnJvbS5sZW5ndGgsIGFyOyBpIDwgbDsgaSsrKSB7XG4gICAgICAgIGlmIChhciB8fCAhKGkgaW4gZnJvbSkpIHtcbiAgICAgICAgICAgIGlmICghYXIpIGFyID0gQXJyYXkucHJvdG90eXBlLnNsaWNlLmNhbGwoZnJvbSwgMCwgaSk7XG4gICAgICAgICAgICBhcltpXSA9IGZyb21baV07XG4gICAgICAgIH1cbiAgICB9XG4gICAgcmV0dXJuIHRvLmNvbmNhdChhciB8fCBBcnJheS5wcm90b3R5cGUuc2xpY2UuY2FsbChmcm9tKSk7XG59O1xuZXhwb3J0cy5fX2VzTW9kdWxlID0gdHJ1ZTtcbmV4cG9ydHMucmViaW5kQnVsa0FjdGlvbnNFdmVudExpc3RlbmVycyA9IGV4cG9ydHMuYWRkQnVsa0FjdGlvbkxpc3RlbmVycyA9IHZvaWQgMDtcbnZhciByYW5nZV8xID0gcmVxdWlyZShcIi4uL3V0aWxzL3JhbmdlXCIpO1xudmFyIEJVTEtfQUNUSU9OX1BBR0VfQ0hFQ0tCT1hfSU5QVVQgPSAnW2RhdGEtYnVsay1hY3Rpb24tY2hlY2tib3hdJztcbnZhciBCVUxLX0FDVElPTl9TRUxFQ1RfQUxMX0NIRUNLQk9YID0gJ1tkYXRhLWJ1bGstYWN0aW9uLXNlbGVjdC1hbGwtY2hlY2tib3hdJztcbnZhciBCVUxLX0FDVElPTlNfQ0hFQ0tCT1hfUEFSRU5UID0gJ1tkYXRhLWJ1bGstYWN0aW9uLXBhcmVudC1pZF0nO1xudmFyIEJVTEtfQUNUSU9OX0ZPT1RFUiA9ICdbZGF0YS1idWxrLWFjdGlvbi1mb290ZXJdJztcbnZhciBCVUxLX0FDVElPTl9OVU1fT0JKRUNUUyA9ICdbZGF0YS1idWxrLWFjdGlvbi1udW0tb2JqZWN0c10nO1xudmFyIEJVTEtfQUNUSU9OX05VTV9PQkpFQ1RTX0lOX0xJU1RJTkcgPSAnW2RhdGEtYnVsay1hY3Rpb24tbnVtLW9iamVjdHMtaW4tbGlzdGluZ10nO1xudmFyIE1PUkVfQUNUSU9OU19EUk9QRE9XTl9CVVRUT05fU0VMRUNUT1IgPSAnLmFjdGlvbnMgW2RhdGEtZHJvcGRvd25dJztcbnZhciBjaGVja2VkU3RhdGUgPSB7fTtcbi8qKlxuICogVG9nZ2xlcyB0aGUgJ21vcmUnIGRyb3Bkb3duIGJ1dHRvbiBpbiBsaXN0aW5nIHBhZ2VzLlxuICogQHBhcmFtIHtib29sZWFufSBzaG93IC0gRGV0ZXJtaW5lcyBpZiB0aGUgYnV0dG9uIHNob3VsZCBiZSBzaG93biBvciBub3QuXG4gKi9cbmZ1bmN0aW9uIHRvZ2dsZU1vcmVBY3Rpb25zRHJvcGRvd25CdG4oc2hvdykge1xuICAgIHZhciBtb3JlQWN0aW9uc0Ryb3Bkb3duID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcihNT1JFX0FDVElPTlNfRFJPUERPV05fQlVUVE9OX1NFTEVDVE9SKTtcbiAgICBpZiAobW9yZUFjdGlvbnNEcm9wZG93biAhPT0gbnVsbCkge1xuICAgICAgICBpZiAoc2hvdyA9PT0gdHJ1ZSkge1xuICAgICAgICAgICAgbW9yZUFjdGlvbnNEcm9wZG93bi5jbGFzc0xpc3QucmVtb3ZlKCdoaWRkZW4nKTtcbiAgICAgICAgfVxuICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgIG1vcmVBY3Rpb25zRHJvcGRvd24uY2xhc3NMaXN0LmFkZCgnaGlkZGVuJyk7XG4gICAgICAgIH1cbiAgICB9XG59XG4vKipcbiAqIFV0aWxpdHkgZnVuY3Rpb24gdG8gZ2V0IHRoZSBhcHByb3ByaWF0ZSBzdHJpbmcgZm9yIGRpc3BsYXkgaW4gYWN0aW9uIGJhclxuICovXG5mdW5jdGlvbiBnZXRTdHJpbmdGb3JMaXN0aW5nKGtleSkge1xuICAgIGlmICh3YWd0YWlsQ29uZmlnLlNUUklOR1MuQlVMS19BQ1RJT05TW3dhZ3RhaWxDb25maWcuQlVMS19BQ1RJT05fSVRFTV9UWVBFXSkge1xuICAgICAgICByZXR1cm4gd2FndGFpbENvbmZpZy5TVFJJTkdTLkJVTEtfQUNUSU9OU1t3YWd0YWlsQ29uZmlnLkJVTEtfQUNUSU9OX0lURU1fVFlQRV1ba2V5XTtcbiAgICB9XG4gICAgcmV0dXJuIHdhZ3RhaWxDb25maWcuU1RSSU5HUy5CVUxLX0FDVElPTlMuSVRFTVtrZXldO1xufVxuLyoqXG4gKiBFdmVudCBsaXN0ZW5lciBmb3IgdGhlIGBTZWxlY3QgQWxsYCBjaGVja2JveFxuICovXG5mdW5jdGlvbiBvblNlbGVjdEFsbENoYW5nZShlKSB7XG4gICAgZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbChCVUxLX0FDVElPTl9TRUxFQ1RfQUxMX0NIRUNLQk9YKS5mb3JFYWNoKGZ1bmN0aW9uIChlbCkge1xuICAgICAgICBlbC5jaGVja2VkID0gZS50YXJnZXQuY2hlY2tlZDsgLy8gZXNsaW50LWRpc2FibGUtbGluZSBuby1wYXJhbS1yZWFzc2lnblxuICAgIH0pO1xuICAgIHZhciBjaGFuZ2VFdmVudCA9IG5ldyBFdmVudCgnY2hhbmdlJyk7XG4gICAgZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbChCVUxLX0FDVElPTl9QQUdFX0NIRUNLQk9YX0lOUFVUKS5mb3JFYWNoKGZ1bmN0aW9uIChlbCkge1xuICAgICAgICBpZiAoZWwuY2hlY2tlZCAhPT0gZS50YXJnZXQuY2hlY2tlZCkge1xuICAgICAgICAgICAgLy8gZXNsaW50LWRpc2FibGUtbmV4dC1saW5lIG5vLXBhcmFtLXJlYXNzaWduXG4gICAgICAgICAgICBlbC5jaGVja2VkID0gZS50YXJnZXQuY2hlY2tlZDtcbiAgICAgICAgICAgIGlmIChlLnRhcmdldC5jaGVja2VkKSB7XG4gICAgICAgICAgICAgICAgZWwuZGlzcGF0Y2hFdmVudChjaGFuZ2VFdmVudCk7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgICAgICBlbC5jbGFzc0xpc3QucmVtb3ZlKCdzaG93Jyk7XG4gICAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICB9KTtcbiAgICBpZiAoIWUudGFyZ2V0LmNoZWNrZWQpIHtcbiAgICAgICAgdG9nZ2xlTW9yZUFjdGlvbnNEcm9wZG93bkJ0bih0cnVlKTtcbiAgICAgICAgLy8gd2hlbiBkZXNlbGVjdGluZyBhbGwgY2hlY2tib3gsIHNpbXBseSBoaWRlIHRoZSBmb290ZXIgZm9yIHNtb290aCB0cmFuc2l0aW9uXG4gICAgICAgIGNoZWNrZWRTdGF0ZS5jaGVja2VkT2JqZWN0cy5jbGVhcigpO1xuICAgICAgICBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKEJVTEtfQUNUSU9OX0ZPT1RFUikuY2xhc3NMaXN0LmFkZCgnaGlkZGVuJyk7XG4gICAgfVxuICAgIGVsc2Uge1xuICAgICAgICB0b2dnbGVNb3JlQWN0aW9uc0Ryb3Bkb3duQnRuKGZhbHNlKTtcbiAgICB9XG59XG4vKipcbiAqIEV2ZW50IGxpc3RlbmVyIGZvciBjbGlja2luZyBpbmRpdmlkdWFsIGNoZWNrYm94IGFuZCBjaGVja2luZyBpZiBzaGlmdCBrZXkgaXMgcHJlc3NlZFxuICpcbiAqIEBwYXJhbSB7RXZlbnR9IGV2ZW50XG4gKi9cbmZ1bmN0aW9uIG9uQ2xpY2tJbmRpdmlkdWFsQ2hlY2tib3goZXZlbnQpIHtcbiAgICBpZiAoZXZlbnQuc2hpZnRLZXkgJiYgY2hlY2tlZFN0YXRlLnByZXZDaGVja2VkT2JqZWN0KSB7XG4gICAgICAgIHZhciBpbmRpdmlkdWFsQ2hlY2tib3hMaXN0XzEgPSBfX3NwcmVhZEFycmF5KFtdLCBfX3JlYWQoZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbChCVUxLX0FDVElPTl9QQUdFX0NIRUNLQk9YX0lOUFVUKSksIGZhbHNlKTtcbiAgICAgICAgdmFyIHByZXZDaGVja2VkT2JqZWN0SW5kZXhfMSA9IGluZGl2aWR1YWxDaGVja2JveExpc3RfMS5maW5kSW5kZXgoZnVuY3Rpb24gKGVsKSB7IHJldHVybiBlbC5kYXRhc2V0Lm9iamVjdElkID09PSBjaGVja2VkU3RhdGUucHJldkNoZWNrZWRPYmplY3Q7IH0pO1xuICAgICAgICB2YXIgc2hpZnRDbGlja2VkT2JqZWN0SW5kZXggPSBpbmRpdmlkdWFsQ2hlY2tib3hMaXN0XzEuZmluZEluZGV4KGZ1bmN0aW9uIChlbCkgeyByZXR1cm4gZWwuZGF0YXNldC5vYmplY3RJZCA9PT0gZXZlbnQudGFyZ2V0LmRhdGFzZXQub2JqZWN0SWQ7IH0pO1xuICAgICAgICB2YXIgc3RhcnRpbmdJbmRleCA9IChwcmV2Q2hlY2tlZE9iamVjdEluZGV4XzEgPiBzaGlmdENsaWNrZWRPYmplY3RJbmRleFxuICAgICAgICAgICAgPyBzaGlmdENsaWNrZWRPYmplY3RJbmRleFxuICAgICAgICAgICAgOiBwcmV2Q2hlY2tlZE9iamVjdEluZGV4XzEpICsgMTtcbiAgICAgICAgdmFyIGVuZGluZ0luZGV4ID0gcHJldkNoZWNrZWRPYmplY3RJbmRleF8xIDw9IHNoaWZ0Q2xpY2tlZE9iamVjdEluZGV4XG4gICAgICAgICAgICA/IHNoaWZ0Q2xpY2tlZE9iamVjdEluZGV4XG4gICAgICAgICAgICA6IHByZXZDaGVja2VkT2JqZWN0SW5kZXhfMTtcbiAgICAgICAgKDAsIHJhbmdlXzEucmFuZ2UpKHN0YXJ0aW5nSW5kZXgsIGVuZGluZ0luZGV4KS5mb3JFYWNoKGZ1bmN0aW9uIChpKSB7XG4gICAgICAgICAgICB2YXIgY2hhbmdlRXZlbnQgPSBuZXcgRXZlbnQoJ2NoYW5nZScpO1xuICAgICAgICAgICAgaW5kaXZpZHVhbENoZWNrYm94TGlzdF8xW2ldLmNoZWNrZWQgPVxuICAgICAgICAgICAgICAgIGluZGl2aWR1YWxDaGVja2JveExpc3RfMVtwcmV2Q2hlY2tlZE9iamVjdEluZGV4XzFdLmNoZWNrZWQ7XG4gICAgICAgICAgICBpbmRpdmlkdWFsQ2hlY2tib3hMaXN0XzFbaV0uZGlzcGF0Y2hFdmVudChjaGFuZ2VFdmVudCk7XG4gICAgICAgIH0pO1xuICAgICAgICBjaGVja2VkU3RhdGUucHJldkNoZWNrZWRPYmplY3QgPSBldmVudC50YXJnZXQuZGF0YXNldC5vYmplY3RJZDtcbiAgICB9XG59XG4vKipcbiAqIEV2ZW50IGxpc3RlbmVyIGZvciBpbmRpdmlkdWFsIGNoZWNrYm94XG4gKi9cbmZ1bmN0aW9uIG9uU2VsZWN0SW5kaXZpZHVhbENoZWNrYm94KGUpIHtcbiAgICBpZiAoY2hlY2tlZFN0YXRlLnNlbGVjdEFsbEluTGlzdGluZylcbiAgICAgICAgY2hlY2tlZFN0YXRlLnNlbGVjdEFsbEluTGlzdGluZyA9IGZhbHNlO1xuICAgIHZhciBwcmV2TGVuZ3RoID0gY2hlY2tlZFN0YXRlLmNoZWNrZWRPYmplY3RzLnNpemU7XG4gICAgaWYgKGUudGFyZ2V0LmNoZWNrZWQpIHtcbiAgICAgICAgY2hlY2tlZFN0YXRlLmNoZWNrZWRPYmplY3RzLmFkZChlLnRhcmdldC5kYXRhc2V0Lm9iamVjdElkKTtcbiAgICB9XG4gICAgZWxzZSB7XG4gICAgICAgIC8qIHVuY2hlY2tzIGBTZWxlY3QgYWxsYCBjaGVja2JveCBhcyBzb29uIGFzIG9uZSBwYWdlIGlzIHVuY2hlY2tlZCAqL1xuICAgICAgICBkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKEJVTEtfQUNUSU9OX1NFTEVDVF9BTExfQ0hFQ0tCT1gpLmZvckVhY2goZnVuY3Rpb24gKGVsKSB7XG4gICAgICAgICAgICBlbC5jaGVja2VkID0gZmFsc2U7IC8vIGVzbGludC1kaXNhYmxlLWxpbmUgbm8tcGFyYW0tcmVhc3NpZ25cbiAgICAgICAgfSk7XG4gICAgICAgIGNoZWNrZWRTdGF0ZS5jaGVja2VkT2JqZWN0c1tcImRlbGV0ZVwiXShlLnRhcmdldC5kYXRhc2V0Lm9iamVjdElkKTtcbiAgICB9XG4gICAgdmFyIG51bUNoZWNrZWRPYmplY3RzID0gY2hlY2tlZFN0YXRlLmNoZWNrZWRPYmplY3RzLnNpemU7XG4gICAgaWYgKG51bUNoZWNrZWRPYmplY3RzID09PSAwKSB7XG4gICAgICAgIC8qIHdoZW4gYWxsIGNoZWNrYm94ZXMgYXJlIHVuY2hlY2tlZCAqL1xuICAgICAgICB0b2dnbGVNb3JlQWN0aW9uc0Ryb3Bkb3duQnRuKHRydWUpO1xuICAgICAgICBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKEJVTEtfQUNUSU9OX0ZPT1RFUikuY2xhc3NMaXN0LmFkZCgnaGlkZGVuJyk7XG4gICAgICAgIGRvY3VtZW50XG4gICAgICAgICAgICAucXVlcnlTZWxlY3RvckFsbChCVUxLX0FDVElPTl9QQUdFX0NIRUNLQk9YX0lOUFVUKVxuICAgICAgICAgICAgLmZvckVhY2goZnVuY3Rpb24gKGVsKSB7IHJldHVybiBlbC5jbGFzc0xpc3QucmVtb3ZlKCdzaG93Jyk7IH0pO1xuICAgIH1cbiAgICBlbHNlIGlmIChudW1DaGVja2VkT2JqZWN0cyA9PT0gMSAmJiBwcmV2TGVuZ3RoID09PSAwKSB7XG4gICAgICAgIC8qIHdoZW4gMSBjaGVja2JveCBpcyBjaGVja2VkIGZvciB0aGUgZmlyc3QgdGltZSAqL1xuICAgICAgICB0b2dnbGVNb3JlQWN0aW9uc0Ryb3Bkb3duQnRuKGZhbHNlKTtcbiAgICAgICAgZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbChCVUxLX0FDVElPTl9QQUdFX0NIRUNLQk9YX0lOUFVUKS5mb3JFYWNoKGZ1bmN0aW9uIChlbCkge1xuICAgICAgICAgICAgZWwuY2xhc3NMaXN0LmFkZCgnc2hvdycpO1xuICAgICAgICB9KTtcbiAgICAgICAgZG9jdW1lbnQucXVlcnlTZWxlY3RvcihCVUxLX0FDVElPTl9GT09URVIpLmNsYXNzTGlzdC5yZW1vdmUoJ2hpZGRlbicpO1xuICAgIH1cbiAgICBpZiAobnVtQ2hlY2tlZE9iamVjdHMgPT09IGNoZWNrZWRTdGF0ZS5udW1PYmplY3RzKSB7XG4gICAgICAgIC8qIHdoZW4gYWxsIGNoZWNrYm94ZXMgaW4gdGhlIHBhZ2UgYXJlIGNoZWNrZWQgKi9cbiAgICAgICAgZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbChCVUxLX0FDVElPTl9TRUxFQ1RfQUxMX0NIRUNLQk9YKS5mb3JFYWNoKGZ1bmN0aW9uIChlbCkge1xuICAgICAgICAgICAgZWwuY2hlY2tlZCA9IHRydWU7IC8vIGVzbGludC1kaXNhYmxlLWxpbmUgbm8tcGFyYW0tcmVhc3NpZ25cbiAgICAgICAgfSk7XG4gICAgICAgIGlmIChjaGVja2VkU3RhdGUuc2hvdWxkU2hvd0FsbEluTGlzdGluZ1RleHQpIHtcbiAgICAgICAgICAgIGRvY3VtZW50XG4gICAgICAgICAgICAgICAgLnF1ZXJ5U2VsZWN0b3IoQlVMS19BQ1RJT05fTlVNX09CSkVDVFNfSU5fTElTVElORylcbiAgICAgICAgICAgICAgICAuY2xhc3NMaXN0LnJlbW92ZSgndS1oaWRkZW4nKTtcbiAgICAgICAgfVxuICAgIH1cbiAgICBlbHNlIGlmIChjaGVja2VkU3RhdGUuc2hvdWxkU2hvd0FsbEluTGlzdGluZ1RleHQpIHtcbiAgICAgICAgZG9jdW1lbnRcbiAgICAgICAgICAgIC5xdWVyeVNlbGVjdG9yKEJVTEtfQUNUSU9OX05VTV9PQkpFQ1RTX0lOX0xJU1RJTkcpXG4gICAgICAgICAgICAuY2xhc3NMaXN0LmFkZCgndS1oaWRkZW4nKTtcbiAgICB9XG4gICAgaWYgKG51bUNoZWNrZWRPYmplY3RzID4gMCkge1xuICAgICAgICAvKiBVcGRhdGUgdGV4dCBvbiBudW1iZXIgb2YgcGFnZXMgKi9cbiAgICAgICAgdmFyIG51bU9iamVjdHNTZWxlY3RlZCA9ICcnO1xuICAgICAgICBpZiAobnVtQ2hlY2tlZE9iamVjdHMgPT09IDEpIHtcbiAgICAgICAgICAgIG51bU9iamVjdHNTZWxlY3RlZCA9IGdldFN0cmluZ0Zvckxpc3RpbmcoJ1NJTkdVTEFSJyk7XG4gICAgICAgIH1cbiAgICAgICAgZWxzZSBpZiAobnVtQ2hlY2tlZE9iamVjdHMgPT09IGNoZWNrZWRTdGF0ZS5udW1PYmplY3RzKSB7XG4gICAgICAgICAgICBudW1PYmplY3RzU2VsZWN0ZWQgPSBnZXRTdHJpbmdGb3JMaXN0aW5nKCdBTEwnKS5yZXBsYWNlKCclKG9iamVjdHMpcycsIG51bUNoZWNrZWRPYmplY3RzKTtcbiAgICAgICAgfVxuICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgIG51bU9iamVjdHNTZWxlY3RlZCA9IGdldFN0cmluZ0Zvckxpc3RpbmcoJ1BMVVJBTCcpLnJlcGxhY2UoJyUob2JqZWN0cylzJywgbnVtQ2hlY2tlZE9iamVjdHMpO1xuICAgICAgICB9XG4gICAgICAgIGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoQlVMS19BQ1RJT05fTlVNX09CSkVDVFMpLnRleHRDb250ZW50ID1cbiAgICAgICAgICAgIG51bU9iamVjdHNTZWxlY3RlZDtcbiAgICB9XG4gICAgLy8gVXBkYXRpbmcgcHJldmlvdXNseSBjaGVja2VkIG9iamVjdFxuICAgIGNoZWNrZWRTdGF0ZS5wcmV2Q2hlY2tlZE9iamVjdCA9IGUudGFyZ2V0LmRhdGFzZXQub2JqZWN0SWQ7XG59XG4vKipcbiAqIEV2ZW50IGxpc3RlbmVyIHRvIHNlbGVjdCBhbGwgb2JqZWN0cyBpbiBsaXN0aW5nXG4gKi9cbmZ1bmN0aW9uIG9uQ2xpY2tTZWxlY3RBbGxJbkxpc3RpbmcoZSkge1xuICAgIGUucHJldmVudERlZmF1bHQoKTtcbiAgICBjaGVja2VkU3RhdGUuc2VsZWN0QWxsSW5MaXN0aW5nID0gdHJ1ZTtcbiAgICBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKEJVTEtfQUNUSU9OX05VTV9PQkpFQ1RTKS50ZXh0Q29udGVudCA9IFwiXCIuY29uY2F0KGdldFN0cmluZ0Zvckxpc3RpbmcoJ0FMTF9JTl9MSVNUSU5HJyksIFwiLlwiKTtcbiAgICBkb2N1bWVudFxuICAgICAgICAucXVlcnlTZWxlY3RvcihCVUxLX0FDVElPTl9OVU1fT0JKRUNUU19JTl9MSVNUSU5HKVxuICAgICAgICAuY2xhc3NMaXN0LmFkZCgndS1oaWRkZW4nKTtcbn1cbi8qKlxuICogRXZlbnQgbGlzdGVuZXIgZm9yIGJ1bGsgYWN0aW9ucyB3aGljaCBhcHBlbmRzIHNlbGVjdGVkIGlkcyB0byB0aGUgY29ycmVzcG9uZGluZyBhY3Rpb24gdXJsXG4gKi9cbmZ1bmN0aW9uIG9uQ2xpY2tBY3Rpb25CdXR0b24oZSkge1xuICAgIGUucHJldmVudERlZmF1bHQoKTtcbiAgICB2YXIgdXJsID0gZS50YXJnZXQuZ2V0QXR0cmlidXRlKCdocmVmJyk7XG4gICAgdmFyIHVybFBhcmFtcyA9IG5ldyBVUkxTZWFyY2hQYXJhbXMod2luZG93LmxvY2F0aW9uLnNlYXJjaCk7XG4gICAgaWYgKGNoZWNrZWRTdGF0ZS5zZWxlY3RBbGxJbkxpc3RpbmcpIHtcbiAgICAgICAgdXJsUGFyYW1zLmFwcGVuZCgnaWQnLCAnYWxsJyk7XG4gICAgICAgIHZhciBwYXJlbnRFbGVtZW50ID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcihCVUxLX0FDVElPTlNfQ0hFQ0tCT1hfUEFSRU5UKTtcbiAgICAgICAgaWYgKHBhcmVudEVsZW1lbnQpIHtcbiAgICAgICAgICAgIHZhciBwYXJlbnRQYWdlSWQgPSBwYXJlbnRFbGVtZW50LmRhdGFzZXQuYnVsa0FjdGlvblBhcmVudElkO1xuICAgICAgICAgICAgdXJsUGFyYW1zLmFwcGVuZCgnY2hpbGRPZicsIHBhcmVudFBhZ2VJZCk7XG4gICAgICAgIH1cbiAgICB9XG4gICAgZWxzZSB7XG4gICAgICAgIGNoZWNrZWRTdGF0ZS5jaGVja2VkT2JqZWN0cy5mb3JFYWNoKGZ1bmN0aW9uIChvYmplY3RJZCkge1xuICAgICAgICAgICAgdXJsUGFyYW1zLmFwcGVuZCgnaWQnLCBvYmplY3RJZCk7XG4gICAgICAgIH0pO1xuICAgIH1cbiAgICB3aW5kb3cubG9jYXRpb24uaHJlZiA9IFwiXCIuY29uY2F0KHVybCwgXCImXCIpLmNvbmNhdCh1cmxQYXJhbXMudG9TdHJpbmcoKSk7XG59XG4vKipcbiAqIEFkZHMgYWxsIGV2ZW50IGxpc3RlbmVyc1xuICovXG5mdW5jdGlvbiBhZGRCdWxrQWN0aW9uTGlzdGVuZXJzKCkge1xuICAgIGNoZWNrZWRTdGF0ZSA9IHtcbiAgICAgICAgY2hlY2tlZE9iamVjdHM6IG5ldyBTZXQoKSxcbiAgICAgICAgbnVtT2JqZWN0czogMCxcbiAgICAgICAgc2VsZWN0QWxsSW5MaXN0aW5nOiBmYWxzZSxcbiAgICAgICAgc2hvdWxkU2hvd0FsbEluTGlzdGluZ1RleHQ6IHRydWUsXG4gICAgICAgIHByZXZDaGVja2VkT2JqZWN0OiBudWxsXG4gICAgfTtcbiAgICB2YXIgY2hhbmdlRXZlbnQgPSBuZXcgRXZlbnQoJ2NoYW5nZScpO1xuICAgIGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoQlVMS19BQ1RJT05fUEFHRV9DSEVDS0JPWF9JTlBVVCkuZm9yRWFjaChmdW5jdGlvbiAoZWwpIHtcbiAgICAgICAgY2hlY2tlZFN0YXRlLm51bU9iamVjdHMgKz0gMTtcbiAgICAgICAgZWwuYWRkRXZlbnRMaXN0ZW5lcignY2hhbmdlJywgb25TZWxlY3RJbmRpdmlkdWFsQ2hlY2tib3gpO1xuICAgICAgICBlbC5hZGRFdmVudExpc3RlbmVyKCdjbGljaycsIG9uQ2xpY2tJbmRpdmlkdWFsQ2hlY2tib3gpO1xuICAgIH0pO1xuICAgIGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoQlVMS19BQ1RJT05fU0VMRUNUX0FMTF9DSEVDS0JPWCkuZm9yRWFjaChmdW5jdGlvbiAoZWwpIHtcbiAgICAgICAgZWwuYWRkRXZlbnRMaXN0ZW5lcignY2hhbmdlJywgb25TZWxlY3RBbGxDaGFuZ2UpO1xuICAgIH0pO1xuICAgIGRvY3VtZW50XG4gICAgICAgIC5xdWVyeVNlbGVjdG9yQWxsKFwiXCIuY29uY2F0KEJVTEtfQUNUSU9OX0ZPT1RFUiwgXCIgLmJ1bGstYWN0aW9uLWJ0blwiKSlcbiAgICAgICAgLmZvckVhY2goZnVuY3Rpb24gKGVsZW0pIHsgcmV0dXJuIGVsZW0uYWRkRXZlbnRMaXN0ZW5lcignY2xpY2snLCBvbkNsaWNrQWN0aW9uQnV0dG9uKTsgfSk7XG4gICAgdmFyIHNlbGVjdEFsbEluTGlzdGluZ1RleHQgPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKEJVTEtfQUNUSU9OX05VTV9PQkpFQ1RTX0lOX0xJU1RJTkcpO1xuICAgIGlmIChzZWxlY3RBbGxJbkxpc3RpbmdUZXh0KVxuICAgICAgICBzZWxlY3RBbGxJbkxpc3RpbmdUZXh0LmFkZEV2ZW50TGlzdGVuZXIoJ2NsaWNrJywgb25DbGlja1NlbGVjdEFsbEluTGlzdGluZyk7XG4gICAgZWxzZVxuICAgICAgICBjaGVja2VkU3RhdGUuc2hvdWxkU2hvd0FsbEluTGlzdGluZ1RleHQgPSBmYWxzZTtcbiAgICBkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKEJVTEtfQUNUSU9OX1BBR0VfQ0hFQ0tCT1hfSU5QVVQpLmZvckVhY2goZnVuY3Rpb24gKGVsKSB7XG4gICAgICAgIGlmIChlbC5jaGVja2VkKSB7XG4gICAgICAgICAgICBlbC5kaXNwYXRjaEV2ZW50KGNoYW5nZUV2ZW50KTtcbiAgICAgICAgfVxuICAgIH0pO1xufVxuZXhwb3J0cy5hZGRCdWxrQWN0aW9uTGlzdGVuZXJzID0gYWRkQnVsa0FjdGlvbkxpc3RlbmVycztcbmZ1bmN0aW9uIHJlYmluZEJ1bGtBY3Rpb25zRXZlbnRMaXN0ZW5lcnMoKSB7XG4gICAgLy8gd2hlbiBkZXNlbGVjdGluZyBhbGwgY2hlY2tib3gsIHNpbXBseSBoaWRlIHRoZSBmb290ZXIgZm9yIHNtb290aCB0cmFuc2l0aW9uXG4gICAgZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbChCVUxLX0FDVElPTl9TRUxFQ1RfQUxMX0NIRUNLQk9YKS5mb3JFYWNoKGZ1bmN0aW9uIChlbCkge1xuICAgICAgICBlbC5jaGVja2VkID0gZmFsc2U7IC8vIGVzbGludC1kaXNhYmxlLWxpbmUgbm8tcGFyYW0tcmVhc3NpZ25cbiAgICB9KTtcbiAgICBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKEJVTEtfQUNUSU9OX0ZPT1RFUikuY2xhc3NMaXN0LmFkZCgnaGlkZGVuJyk7XG4gICAgZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbChCVUxLX0FDVElPTl9TRUxFQ1RfQUxMX0NIRUNLQk9YKS5mb3JFYWNoKGZ1bmN0aW9uIChlbCkge1xuICAgICAgICAvLyByZW1vdmUgYWxyZWFkeSBhdHRhY2hlZCBldmVudCBsaXN0ZW5lciBmaXJzdFxuICAgICAgICBlbC5yZW1vdmVFdmVudExpc3RlbmVyKCdjaGFuZ2UnLCBvblNlbGVjdEFsbENoYW5nZSk7XG4gICAgICAgIGVsLmFkZEV2ZW50TGlzdGVuZXIoJ2NoYW5nZScsIG9uU2VsZWN0QWxsQ2hhbmdlKTtcbiAgICB9KTtcbiAgICBjaGVja2VkU3RhdGUuY2hlY2tlZE9iamVjdHMuY2xlYXIoKTtcbiAgICBjaGVja2VkU3RhdGUubnVtT2JqZWN0cyA9IDA7XG4gICAgZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbChCVUxLX0FDVElPTl9QQUdFX0NIRUNLQk9YX0lOUFVUKS5mb3JFYWNoKGZ1bmN0aW9uIChlbCkge1xuICAgICAgICBjaGVja2VkU3RhdGUubnVtT2JqZWN0cyArPSAxO1xuICAgICAgICBlbC5hZGRFdmVudExpc3RlbmVyKCdjaGFuZ2UnLCBvblNlbGVjdEluZGl2aWR1YWxDaGVja2JveCk7XG4gICAgfSk7XG59XG5leHBvcnRzLnJlYmluZEJ1bGtBY3Rpb25zRXZlbnRMaXN0ZW5lcnMgPSByZWJpbmRCdWxrQWN0aW9uc0V2ZW50TGlzdGVuZXJzO1xuIl0sIm5hbWVzIjpbXSwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///./client/src/includes/bulk-actions.js\n");

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
/******/ 			"bulk-actions": 0
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
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["wagtail/admin/static/wagtailadmin/js/vendor"], () => (__webpack_require__("./client/src/entrypoints/admin/bulk-actions.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;