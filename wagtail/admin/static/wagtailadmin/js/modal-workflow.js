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

/***/ "./client/src/entrypoints/admin/modal-workflow.js":
/*!********************************************************!*\
  !*** ./client/src/entrypoints/admin/modal-workflow.js ***!
  \********************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

eval("\n/* A framework for modal popups that are loaded via AJAX, allowing navigation to other\nsubpages to happen within the lightbox, and returning a response to the calling page,\npossibly after several navigation steps\n*/\nvar __importDefault = (this && this.__importDefault) || function (mod) {\n    return (mod && mod.__esModule) ? mod : { \"default\": mod };\n};\nexports.__esModule = true;\nvar jquery_1 = __importDefault(__webpack_require__(/*! jquery */ \"jquery\"));\nvar noop_1 = __webpack_require__(/*! ../../utils/noop */ \"./client/src/utils/noop.ts\");\nvar gettext_1 = __webpack_require__(/*! ../../utils/gettext */ \"./client/src/utils/gettext.ts\");\n/* eslint-disable */\nfunction ModalWorkflow(opts) {\n    /* options passed in 'opts':\n      'url' (required): URL to the view that will be loaded into the dialog.\n        If not provided and dialogId is given, the dialog component's data-url attribute is used instead.\n      'dialogId' (optional): the id of the dialog component to use instead of the Bootstrap modal\n      'responses' (optional): dict of callbacks to be called when the modal content\n        calls modal.respond(callbackName, params)\n      'onload' (optional): dict of callbacks to be called when loading a step of the workflow.\n        The 'step' field in the response identifies the callback to call, passing it the\n        modal object and response data as arguments\n    */\n    var self = {};\n    var responseCallbacks = opts.responses || {};\n    var errorCallback = opts.onError || noop_1.noop;\n    var useDialog = !!opts.dialogId;\n    if (useDialog) {\n        self.dialog = document.getElementById(opts.dialogId);\n        self.url = opts.url || self.dialog.dataset.url;\n        self.body = self.dialog.querySelector('[data-dialog-body]');\n        // Clear the dialog body as it may have been populated previously\n        self.body.innerHTML = '';\n    }\n    else {\n        /* remove any previous modals before continuing (closing doesn't remove them from the dom) */\n        (0, jquery_1[\"default\"])('body > .modal').remove();\n        // disable the trigger element so it cannot be clicked twice while modal is loading\n        self.triggerElement = document.activeElement;\n        self.triggerElement.setAttribute('disabled', true);\n        // set default contents of container\n        var iconClose = '<svg class=\"icon icon-cross\" aria-hidden=\"true\"><use href=\"#icon-cross\"></use></svg>';\n        self.container = (0, jquery_1[\"default\"])('<div class=\"modal fade\" tabindex=\"-1\" role=\"dialog\" aria-hidden=\"true\">\\n  <div class=\"modal-dialog\">\\n    <div class=\"modal-content\">\\n      <button type=\"button\" class=\"button close button--icon text-replace\" data-dismiss=\"modal\">' +\n            iconClose +\n            (0, gettext_1.gettext)('Close') +\n            '</button>\\n      <div class=\"modal-body\"></div>\\n    </div><!-- /.modal-content -->\\n  </div><!-- /.modal-dialog -->\\n</div>');\n        // add container to body and hide it, so content can be added to it before display\n        (0, jquery_1[\"default\"])('body').append(self.container);\n        self.container.modal('hide');\n        // add listener - once modal is about to be hidden, re-enable the trigger\n        self.container.on('hide.bs.modal', function () {\n            self.triggerElement.removeAttribute('disabled');\n        });\n        // add listener - once modal is fully hidden (closed & css transitions end) - re-focus on trigger and remove from DOM\n        self.container.on('hidden.bs.modal', function () {\n            self.triggerElement.focus();\n            self.container.remove();\n        });\n        self.url = opts.url;\n        self.body = self.container.find('.modal-body');\n    }\n    self.loadUrl = function (url, urlParams) {\n        jquery_1[\"default\"].get(url, urlParams, self.loadResponseText, 'text').fail(errorCallback);\n    };\n    self.postForm = function (url, formData) {\n        jquery_1[\"default\"].post(url, formData, self.loadResponseText, 'text').fail(errorCallback);\n    };\n    self.ajaxifyForm = function (formSelector) {\n        (0, jquery_1[\"default\"])(formSelector).each(function () {\n            var action = this.action;\n            if (this.method.toLowerCase() === 'get') {\n                (0, jquery_1[\"default\"])(this).on('submit', function () {\n                    self.loadUrl(action, (0, jquery_1[\"default\"])(this).serialize());\n                    return false;\n                });\n            }\n            else {\n                (0, jquery_1[\"default\"])(this).on('submit', function () {\n                    self.postForm(action, (0, jquery_1[\"default\"])(this).serialize());\n                    return false;\n                });\n            }\n        });\n    };\n    self.loadResponseText = function (responseText) {\n        var response = JSON.parse(responseText);\n        self.loadBody(response);\n    };\n    self.loadBody = function (response) {\n        if (response.html) {\n            // if response contains an 'html' item, replace modal body with it\n            if (useDialog) {\n                self.body.innerHTML = response.html;\n            }\n            else {\n                self.body.html(response.html);\n                self.container.modal('show');\n            }\n        }\n        /* If response contains a 'step' identifier, and that identifier is found in\n        the onload dict, call that onload handler */\n        if (opts.onload && response.step && response.step in opts.onload) {\n            opts.onload[response.step](self, response);\n        }\n    };\n    self.respond = function (responseType) {\n        if (responseType in responseCallbacks) {\n            var args = Array.prototype.slice.call(arguments, 1);\n            responseCallbacks[responseType].apply(self, args);\n        }\n    };\n    self.close = function () {\n        if (useDialog) {\n            self.dialog.dispatchEvent(new CustomEvent('wagtail:hide'));\n        }\n        else {\n            self.container.modal('hide');\n        }\n    };\n    self.loadUrl(self.url, opts.urlParams);\n    return self;\n}\nwindow.ModalWorkflow = ModalWorkflow;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL21vZGFsLXdvcmtmbG93LmpzLmpzIiwibWFwcGluZ3MiOiJBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vd2FndGFpbC8uL2NsaWVudC9zcmMvZW50cnlwb2ludHMvYWRtaW4vbW9kYWwtd29ya2Zsb3cuanM/MjYwZiJdLCJzb3VyY2VzQ29udGVudCI6WyJcInVzZSBzdHJpY3RcIjtcbi8qIEEgZnJhbWV3b3JrIGZvciBtb2RhbCBwb3B1cHMgdGhhdCBhcmUgbG9hZGVkIHZpYSBBSkFYLCBhbGxvd2luZyBuYXZpZ2F0aW9uIHRvIG90aGVyXG5zdWJwYWdlcyB0byBoYXBwZW4gd2l0aGluIHRoZSBsaWdodGJveCwgYW5kIHJldHVybmluZyBhIHJlc3BvbnNlIHRvIHRoZSBjYWxsaW5nIHBhZ2UsXG5wb3NzaWJseSBhZnRlciBzZXZlcmFsIG5hdmlnYXRpb24gc3RlcHNcbiovXG52YXIgX19pbXBvcnREZWZhdWx0ID0gKHRoaXMgJiYgdGhpcy5fX2ltcG9ydERlZmF1bHQpIHx8IGZ1bmN0aW9uIChtb2QpIHtcbiAgICByZXR1cm4gKG1vZCAmJiBtb2QuX19lc01vZHVsZSkgPyBtb2QgOiB7IFwiZGVmYXVsdFwiOiBtb2QgfTtcbn07XG5leHBvcnRzLl9fZXNNb2R1bGUgPSB0cnVlO1xudmFyIGpxdWVyeV8xID0gX19pbXBvcnREZWZhdWx0KHJlcXVpcmUoXCJqcXVlcnlcIikpO1xudmFyIG5vb3BfMSA9IHJlcXVpcmUoXCIuLi8uLi91dGlscy9ub29wXCIpO1xudmFyIGdldHRleHRfMSA9IHJlcXVpcmUoXCIuLi8uLi91dGlscy9nZXR0ZXh0XCIpO1xuLyogZXNsaW50LWRpc2FibGUgKi9cbmZ1bmN0aW9uIE1vZGFsV29ya2Zsb3cob3B0cykge1xuICAgIC8qIG9wdGlvbnMgcGFzc2VkIGluICdvcHRzJzpcbiAgICAgICd1cmwnIChyZXF1aXJlZCk6IFVSTCB0byB0aGUgdmlldyB0aGF0IHdpbGwgYmUgbG9hZGVkIGludG8gdGhlIGRpYWxvZy5cbiAgICAgICAgSWYgbm90IHByb3ZpZGVkIGFuZCBkaWFsb2dJZCBpcyBnaXZlbiwgdGhlIGRpYWxvZyBjb21wb25lbnQncyBkYXRhLXVybCBhdHRyaWJ1dGUgaXMgdXNlZCBpbnN0ZWFkLlxuICAgICAgJ2RpYWxvZ0lkJyAob3B0aW9uYWwpOiB0aGUgaWQgb2YgdGhlIGRpYWxvZyBjb21wb25lbnQgdG8gdXNlIGluc3RlYWQgb2YgdGhlIEJvb3RzdHJhcCBtb2RhbFxuICAgICAgJ3Jlc3BvbnNlcycgKG9wdGlvbmFsKTogZGljdCBvZiBjYWxsYmFja3MgdG8gYmUgY2FsbGVkIHdoZW4gdGhlIG1vZGFsIGNvbnRlbnRcbiAgICAgICAgY2FsbHMgbW9kYWwucmVzcG9uZChjYWxsYmFja05hbWUsIHBhcmFtcylcbiAgICAgICdvbmxvYWQnIChvcHRpb25hbCk6IGRpY3Qgb2YgY2FsbGJhY2tzIHRvIGJlIGNhbGxlZCB3aGVuIGxvYWRpbmcgYSBzdGVwIG9mIHRoZSB3b3JrZmxvdy5cbiAgICAgICAgVGhlICdzdGVwJyBmaWVsZCBpbiB0aGUgcmVzcG9uc2UgaWRlbnRpZmllcyB0aGUgY2FsbGJhY2sgdG8gY2FsbCwgcGFzc2luZyBpdCB0aGVcbiAgICAgICAgbW9kYWwgb2JqZWN0IGFuZCByZXNwb25zZSBkYXRhIGFzIGFyZ3VtZW50c1xuICAgICovXG4gICAgdmFyIHNlbGYgPSB7fTtcbiAgICB2YXIgcmVzcG9uc2VDYWxsYmFja3MgPSBvcHRzLnJlc3BvbnNlcyB8fCB7fTtcbiAgICB2YXIgZXJyb3JDYWxsYmFjayA9IG9wdHMub25FcnJvciB8fCBub29wXzEubm9vcDtcbiAgICB2YXIgdXNlRGlhbG9nID0gISFvcHRzLmRpYWxvZ0lkO1xuICAgIGlmICh1c2VEaWFsb2cpIHtcbiAgICAgICAgc2VsZi5kaWFsb2cgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZChvcHRzLmRpYWxvZ0lkKTtcbiAgICAgICAgc2VsZi51cmwgPSBvcHRzLnVybCB8fCBzZWxmLmRpYWxvZy5kYXRhc2V0LnVybDtcbiAgICAgICAgc2VsZi5ib2R5ID0gc2VsZi5kaWFsb2cucXVlcnlTZWxlY3RvcignW2RhdGEtZGlhbG9nLWJvZHldJyk7XG4gICAgICAgIC8vIENsZWFyIHRoZSBkaWFsb2cgYm9keSBhcyBpdCBtYXkgaGF2ZSBiZWVuIHBvcHVsYXRlZCBwcmV2aW91c2x5XG4gICAgICAgIHNlbGYuYm9keS5pbm5lckhUTUwgPSAnJztcbiAgICB9XG4gICAgZWxzZSB7XG4gICAgICAgIC8qIHJlbW92ZSBhbnkgcHJldmlvdXMgbW9kYWxzIGJlZm9yZSBjb250aW51aW5nIChjbG9zaW5nIGRvZXNuJ3QgcmVtb3ZlIHRoZW0gZnJvbSB0aGUgZG9tKSAqL1xuICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnYm9keSA+IC5tb2RhbCcpLnJlbW92ZSgpO1xuICAgICAgICAvLyBkaXNhYmxlIHRoZSB0cmlnZ2VyIGVsZW1lbnQgc28gaXQgY2Fubm90IGJlIGNsaWNrZWQgdHdpY2Ugd2hpbGUgbW9kYWwgaXMgbG9hZGluZ1xuICAgICAgICBzZWxmLnRyaWdnZXJFbGVtZW50ID0gZG9jdW1lbnQuYWN0aXZlRWxlbWVudDtcbiAgICAgICAgc2VsZi50cmlnZ2VyRWxlbWVudC5zZXRBdHRyaWJ1dGUoJ2Rpc2FibGVkJywgdHJ1ZSk7XG4gICAgICAgIC8vIHNldCBkZWZhdWx0IGNvbnRlbnRzIG9mIGNvbnRhaW5lclxuICAgICAgICB2YXIgaWNvbkNsb3NlID0gJzxzdmcgY2xhc3M9XCJpY29uIGljb24tY3Jvc3NcIiBhcmlhLWhpZGRlbj1cInRydWVcIj48dXNlIGhyZWY9XCIjaWNvbi1jcm9zc1wiPjwvdXNlPjwvc3ZnPic7XG4gICAgICAgIHNlbGYuY29udGFpbmVyID0gKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJzxkaXYgY2xhc3M9XCJtb2RhbCBmYWRlXCIgdGFiaW5kZXg9XCItMVwiIHJvbGU9XCJkaWFsb2dcIiBhcmlhLWhpZGRlbj1cInRydWVcIj5cXG4gIDxkaXYgY2xhc3M9XCJtb2RhbC1kaWFsb2dcIj5cXG4gICAgPGRpdiBjbGFzcz1cIm1vZGFsLWNvbnRlbnRcIj5cXG4gICAgICA8YnV0dG9uIHR5cGU9XCJidXR0b25cIiBjbGFzcz1cImJ1dHRvbiBjbG9zZSBidXR0b24tLWljb24gdGV4dC1yZXBsYWNlXCIgZGF0YS1kaXNtaXNzPVwibW9kYWxcIj4nICtcbiAgICAgICAgICAgIGljb25DbG9zZSArXG4gICAgICAgICAgICAoMCwgZ2V0dGV4dF8xLmdldHRleHQpKCdDbG9zZScpICtcbiAgICAgICAgICAgICc8L2J1dHRvbj5cXG4gICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtYm9keVwiPjwvZGl2PlxcbiAgICA8L2Rpdj48IS0tIC8ubW9kYWwtY29udGVudCAtLT5cXG4gIDwvZGl2PjwhLS0gLy5tb2RhbC1kaWFsb2cgLS0+XFxuPC9kaXY+Jyk7XG4gICAgICAgIC8vIGFkZCBjb250YWluZXIgdG8gYm9keSBhbmQgaGlkZSBpdCwgc28gY29udGVudCBjYW4gYmUgYWRkZWQgdG8gaXQgYmVmb3JlIGRpc3BsYXlcbiAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJ2JvZHknKS5hcHBlbmQoc2VsZi5jb250YWluZXIpO1xuICAgICAgICBzZWxmLmNvbnRhaW5lci5tb2RhbCgnaGlkZScpO1xuICAgICAgICAvLyBhZGQgbGlzdGVuZXIgLSBvbmNlIG1vZGFsIGlzIGFib3V0IHRvIGJlIGhpZGRlbiwgcmUtZW5hYmxlIHRoZSB0cmlnZ2VyXG4gICAgICAgIHNlbGYuY29udGFpbmVyLm9uKCdoaWRlLmJzLm1vZGFsJywgZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgc2VsZi50cmlnZ2VyRWxlbWVudC5yZW1vdmVBdHRyaWJ1dGUoJ2Rpc2FibGVkJyk7XG4gICAgICAgIH0pO1xuICAgICAgICAvLyBhZGQgbGlzdGVuZXIgLSBvbmNlIG1vZGFsIGlzIGZ1bGx5IGhpZGRlbiAoY2xvc2VkICYgY3NzIHRyYW5zaXRpb25zIGVuZCkgLSByZS1mb2N1cyBvbiB0cmlnZ2VyIGFuZCByZW1vdmUgZnJvbSBET01cbiAgICAgICAgc2VsZi5jb250YWluZXIub24oJ2hpZGRlbi5icy5tb2RhbCcsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIHNlbGYudHJpZ2dlckVsZW1lbnQuZm9jdXMoKTtcbiAgICAgICAgICAgIHNlbGYuY29udGFpbmVyLnJlbW92ZSgpO1xuICAgICAgICB9KTtcbiAgICAgICAgc2VsZi51cmwgPSBvcHRzLnVybDtcbiAgICAgICAgc2VsZi5ib2R5ID0gc2VsZi5jb250YWluZXIuZmluZCgnLm1vZGFsLWJvZHknKTtcbiAgICB9XG4gICAgc2VsZi5sb2FkVXJsID0gZnVuY3Rpb24gKHVybCwgdXJsUGFyYW1zKSB7XG4gICAgICAgIGpxdWVyeV8xW1wiZGVmYXVsdFwiXS5nZXQodXJsLCB1cmxQYXJhbXMsIHNlbGYubG9hZFJlc3BvbnNlVGV4dCwgJ3RleHQnKS5mYWlsKGVycm9yQ2FsbGJhY2spO1xuICAgIH07XG4gICAgc2VsZi5wb3N0Rm9ybSA9IGZ1bmN0aW9uICh1cmwsIGZvcm1EYXRhKSB7XG4gICAgICAgIGpxdWVyeV8xW1wiZGVmYXVsdFwiXS5wb3N0KHVybCwgZm9ybURhdGEsIHNlbGYubG9hZFJlc3BvbnNlVGV4dCwgJ3RleHQnKS5mYWlsKGVycm9yQ2FsbGJhY2spO1xuICAgIH07XG4gICAgc2VsZi5hamF4aWZ5Rm9ybSA9IGZ1bmN0aW9uIChmb3JtU2VsZWN0b3IpIHtcbiAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoZm9ybVNlbGVjdG9yKS5lYWNoKGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIHZhciBhY3Rpb24gPSB0aGlzLmFjdGlvbjtcbiAgICAgICAgICAgIGlmICh0aGlzLm1ldGhvZC50b0xvd2VyQ2FzZSgpID09PSAnZ2V0Jykge1xuICAgICAgICAgICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKHRoaXMpLm9uKCdzdWJtaXQnLCBmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICAgICAgICAgIHNlbGYubG9hZFVybChhY3Rpb24sICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKHRoaXMpLnNlcmlhbGl6ZSgpKTtcbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgICAgICAgIH0pO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgZWxzZSB7XG4gICAgICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkodGhpcykub24oJ3N1Ym1pdCcsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgICAgICAgICAgc2VsZi5wb3N0Rm9ybShhY3Rpb24sICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKHRoaXMpLnNlcmlhbGl6ZSgpKTtcbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgICAgICAgIH0pO1xuICAgICAgICAgICAgfVxuICAgICAgICB9KTtcbiAgICB9O1xuICAgIHNlbGYubG9hZFJlc3BvbnNlVGV4dCA9IGZ1bmN0aW9uIChyZXNwb25zZVRleHQpIHtcbiAgICAgICAgdmFyIHJlc3BvbnNlID0gSlNPTi5wYXJzZShyZXNwb25zZVRleHQpO1xuICAgICAgICBzZWxmLmxvYWRCb2R5KHJlc3BvbnNlKTtcbiAgICB9O1xuICAgIHNlbGYubG9hZEJvZHkgPSBmdW5jdGlvbiAocmVzcG9uc2UpIHtcbiAgICAgICAgaWYgKHJlc3BvbnNlLmh0bWwpIHtcbiAgICAgICAgICAgIC8vIGlmIHJlc3BvbnNlIGNvbnRhaW5zIGFuICdodG1sJyBpdGVtLCByZXBsYWNlIG1vZGFsIGJvZHkgd2l0aCBpdFxuICAgICAgICAgICAgaWYgKHVzZURpYWxvZykge1xuICAgICAgICAgICAgICAgIHNlbGYuYm9keS5pbm5lckhUTUwgPSByZXNwb25zZS5odG1sO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgZWxzZSB7XG4gICAgICAgICAgICAgICAgc2VsZi5ib2R5Lmh0bWwocmVzcG9uc2UuaHRtbCk7XG4gICAgICAgICAgICAgICAgc2VsZi5jb250YWluZXIubW9kYWwoJ3Nob3cnKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgfVxuICAgICAgICAvKiBJZiByZXNwb25zZSBjb250YWlucyBhICdzdGVwJyBpZGVudGlmaWVyLCBhbmQgdGhhdCBpZGVudGlmaWVyIGlzIGZvdW5kIGluXG4gICAgICAgIHRoZSBvbmxvYWQgZGljdCwgY2FsbCB0aGF0IG9ubG9hZCBoYW5kbGVyICovXG4gICAgICAgIGlmIChvcHRzLm9ubG9hZCAmJiByZXNwb25zZS5zdGVwICYmIHJlc3BvbnNlLnN0ZXAgaW4gb3B0cy5vbmxvYWQpIHtcbiAgICAgICAgICAgIG9wdHMub25sb2FkW3Jlc3BvbnNlLnN0ZXBdKHNlbGYsIHJlc3BvbnNlKTtcbiAgICAgICAgfVxuICAgIH07XG4gICAgc2VsZi5yZXNwb25kID0gZnVuY3Rpb24gKHJlc3BvbnNlVHlwZSkge1xuICAgICAgICBpZiAocmVzcG9uc2VUeXBlIGluIHJlc3BvbnNlQ2FsbGJhY2tzKSB7XG4gICAgICAgICAgICB2YXIgYXJncyA9IEFycmF5LnByb3RvdHlwZS5zbGljZS5jYWxsKGFyZ3VtZW50cywgMSk7XG4gICAgICAgICAgICByZXNwb25zZUNhbGxiYWNrc1tyZXNwb25zZVR5cGVdLmFwcGx5KHNlbGYsIGFyZ3MpO1xuICAgICAgICB9XG4gICAgfTtcbiAgICBzZWxmLmNsb3NlID0gZnVuY3Rpb24gKCkge1xuICAgICAgICBpZiAodXNlRGlhbG9nKSB7XG4gICAgICAgICAgICBzZWxmLmRpYWxvZy5kaXNwYXRjaEV2ZW50KG5ldyBDdXN0b21FdmVudCgnd2FndGFpbDpoaWRlJykpO1xuICAgICAgICB9XG4gICAgICAgIGVsc2Uge1xuICAgICAgICAgICAgc2VsZi5jb250YWluZXIubW9kYWwoJ2hpZGUnKTtcbiAgICAgICAgfVxuICAgIH07XG4gICAgc2VsZi5sb2FkVXJsKHNlbGYudXJsLCBvcHRzLnVybFBhcmFtcyk7XG4gICAgcmV0dXJuIHNlbGY7XG59XG53aW5kb3cuTW9kYWxXb3JrZmxvdyA9IE1vZGFsV29ya2Zsb3c7XG4iXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/modal-workflow.js\n");

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
/******/ 			"modal-workflow": 0
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
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["wagtail/admin/static/wagtailadmin/js/vendor"], () => (__webpack_require__("./client/src/entrypoints/admin/modal-workflow.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;