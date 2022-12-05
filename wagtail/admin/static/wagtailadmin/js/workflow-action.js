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

/***/ "./client/src/entrypoints/admin/workflow-action.js":
/*!*********************************************************!*\
  !*** ./client/src/entrypoints/admin/workflow-action.js ***!
  \*********************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

eval("\nvar __importDefault = (this && this.__importDefault) || function (mod) {\n    return (mod && mod.__esModule) ? mod : { \"default\": mod };\n};\nexports.__esModule = true;\nvar jquery_1 = __importDefault(__webpack_require__(/*! jquery */ \"jquery\"));\nfunction addHiddenInput(form, name, val) {\n    var element = document.createElement('input');\n    element.type = 'hidden';\n    element.name = name;\n    element.value = val;\n    form.appendChild(element);\n}\n// eslint-disable-next-line no-underscore-dangle\nwindow._addHiddenInput = addHiddenInput;\n/* When a workflow action button is clicked, either show a modal or make a POST request to the workflow action view */\nfunction ActivateWorkflowActionsForDashboard(csrfToken) {\n    var workflowActionElements = document.querySelectorAll('[data-workflow-action-url]');\n    workflowActionElements.forEach(function (buttonElement) {\n        buttonElement.addEventListener('click', function (e) {\n            // Stop the button from submitting the form\n            e.preventDefault();\n            e.stopPropagation();\n            if ('launchModal' in buttonElement.dataset) {\n                // eslint-disable-next-line no-undef\n                ModalWorkflow({\n                    url: buttonElement.dataset.workflowActionUrl,\n                    onload: {\n                        action: function (modal) {\n                            var nextElement = document.createElement('input');\n                            nextElement.type = 'hidden';\n                            nextElement.name = 'next';\n                            nextElement.value = window.location;\n                            (0, jquery_1[\"default\"])('form', modal.body).append(nextElement);\n                            modal.ajaxifyForm((0, jquery_1[\"default\"])('form', modal.body));\n                        },\n                        success: function (modal, jsonData) {\n                            window.location.href = jsonData.redirect;\n                        }\n                    }\n                });\n            }\n            else {\n                // if not opening a modal, submit a POST request to the action url\n                var formElement = document.createElement('form');\n                formElement.action = buttonElement.dataset.workflowActionUrl;\n                formElement.method = 'POST';\n                addHiddenInput(formElement, 'csrfmiddlewaretoken', csrfToken);\n                addHiddenInput(formElement, 'next', window.location);\n                document.body.appendChild(formElement);\n                formElement.submit();\n            }\n        }, { capture: true });\n    });\n}\nwindow.ActivateWorkflowActionsForDashboard =\n    ActivateWorkflowActionsForDashboard;\nfunction ActivateWorkflowActionsForEditView(formSelector) {\n    var form = (0, jquery_1[\"default\"])(formSelector).get(0);\n    var workflowActionElements = document.querySelectorAll('[data-workflow-action-name]');\n    workflowActionElements.forEach(function (buttonElement) {\n        buttonElement.addEventListener('click', function (e) {\n            if ('workflowActionModalUrl' in buttonElement.dataset) {\n                // This action requires opening a modal to collect additional data.\n                // Stop the button from submitting the form\n                e.preventDefault();\n                e.stopPropagation();\n                // open the modal at the given URL\n                // eslint-disable-next-line no-undef\n                ModalWorkflow({\n                    url: buttonElement.dataset.workflowActionModalUrl,\n                    onload: {\n                        action: function (modal) {\n                            modal.ajaxifyForm((0, jquery_1[\"default\"])('form', modal.body));\n                        },\n                        success: function (modal, jsonData) {\n                            // a success response includes the additional data to submit with the edit form\n                            addHiddenInput(form, 'action-workflow-action', 'true');\n                            addHiddenInput(form, 'workflow-action-name', buttonElement.dataset.workflowActionName);\n                            addHiddenInput(form, 'workflow-action-extra-data', JSON.stringify(jsonData.cleaned_data));\n                            // note: need to submit via jQuery (as opposed to form.submit()) so that the onsubmit handler\n                            // that disables the dirty-form prompt doesn't get bypassed\n                            (0, jquery_1[\"default\"])(form).submit();\n                        }\n                    }\n                });\n            }\n            else {\n                // no modal, so let the form submission to the edit view proceed, with additional\n                // hidden inputs to tell it to perform our action\n                addHiddenInput(form, 'action-workflow-action', 'true');\n                addHiddenInput(form, 'workflow-action-name', buttonElement.dataset.workflowActionName);\n            }\n        }, { capture: true });\n    });\n}\nwindow.ActivateWorkflowActionsForEditView = ActivateWorkflowActionsForEditView;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL3dvcmtmbG93LWFjdGlvbi5qcy5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSIsInNvdXJjZXMiOlsid2VicGFjazovL3dhZ3RhaWwvLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL3dvcmtmbG93LWFjdGlvbi5qcz8wY2U0Il0sInNvdXJjZXNDb250ZW50IjpbIlwidXNlIHN0cmljdFwiO1xudmFyIF9faW1wb3J0RGVmYXVsdCA9ICh0aGlzICYmIHRoaXMuX19pbXBvcnREZWZhdWx0KSB8fCBmdW5jdGlvbiAobW9kKSB7XG4gICAgcmV0dXJuIChtb2QgJiYgbW9kLl9fZXNNb2R1bGUpID8gbW9kIDogeyBcImRlZmF1bHRcIjogbW9kIH07XG59O1xuZXhwb3J0cy5fX2VzTW9kdWxlID0gdHJ1ZTtcbnZhciBqcXVlcnlfMSA9IF9faW1wb3J0RGVmYXVsdChyZXF1aXJlKFwianF1ZXJ5XCIpKTtcbmZ1bmN0aW9uIGFkZEhpZGRlbklucHV0KGZvcm0sIG5hbWUsIHZhbCkge1xuICAgIHZhciBlbGVtZW50ID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgnaW5wdXQnKTtcbiAgICBlbGVtZW50LnR5cGUgPSAnaGlkZGVuJztcbiAgICBlbGVtZW50Lm5hbWUgPSBuYW1lO1xuICAgIGVsZW1lbnQudmFsdWUgPSB2YWw7XG4gICAgZm9ybS5hcHBlbmRDaGlsZChlbGVtZW50KTtcbn1cbi8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBuby11bmRlcnNjb3JlLWRhbmdsZVxud2luZG93Ll9hZGRIaWRkZW5JbnB1dCA9IGFkZEhpZGRlbklucHV0O1xuLyogV2hlbiBhIHdvcmtmbG93IGFjdGlvbiBidXR0b24gaXMgY2xpY2tlZCwgZWl0aGVyIHNob3cgYSBtb2RhbCBvciBtYWtlIGEgUE9TVCByZXF1ZXN0IHRvIHRoZSB3b3JrZmxvdyBhY3Rpb24gdmlldyAqL1xuZnVuY3Rpb24gQWN0aXZhdGVXb3JrZmxvd0FjdGlvbnNGb3JEYXNoYm9hcmQoY3NyZlRva2VuKSB7XG4gICAgdmFyIHdvcmtmbG93QWN0aW9uRWxlbWVudHMgPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCdbZGF0YS13b3JrZmxvdy1hY3Rpb24tdXJsXScpO1xuICAgIHdvcmtmbG93QWN0aW9uRWxlbWVudHMuZm9yRWFjaChmdW5jdGlvbiAoYnV0dG9uRWxlbWVudCkge1xuICAgICAgICBidXR0b25FbGVtZW50LmFkZEV2ZW50TGlzdGVuZXIoJ2NsaWNrJywgZnVuY3Rpb24gKGUpIHtcbiAgICAgICAgICAgIC8vIFN0b3AgdGhlIGJ1dHRvbiBmcm9tIHN1Ym1pdHRpbmcgdGhlIGZvcm1cbiAgICAgICAgICAgIGUucHJldmVudERlZmF1bHQoKTtcbiAgICAgICAgICAgIGUuc3RvcFByb3BhZ2F0aW9uKCk7XG4gICAgICAgICAgICBpZiAoJ2xhdW5jaE1vZGFsJyBpbiBidXR0b25FbGVtZW50LmRhdGFzZXQpIHtcbiAgICAgICAgICAgICAgICAvLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgbm8tdW5kZWZcbiAgICAgICAgICAgICAgICBNb2RhbFdvcmtmbG93KHtcbiAgICAgICAgICAgICAgICAgICAgdXJsOiBidXR0b25FbGVtZW50LmRhdGFzZXQud29ya2Zsb3dBY3Rpb25VcmwsXG4gICAgICAgICAgICAgICAgICAgIG9ubG9hZDoge1xuICAgICAgICAgICAgICAgICAgICAgICAgYWN0aW9uOiBmdW5jdGlvbiAobW9kYWwpIHtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICB2YXIgbmV4dEVsZW1lbnQgPSBkb2N1bWVudC5jcmVhdGVFbGVtZW50KCdpbnB1dCcpO1xuICAgICAgICAgICAgICAgICAgICAgICAgICAgIG5leHRFbGVtZW50LnR5cGUgPSAnaGlkZGVuJztcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBuZXh0RWxlbWVudC5uYW1lID0gJ25leHQnO1xuICAgICAgICAgICAgICAgICAgICAgICAgICAgIG5leHRFbGVtZW50LnZhbHVlID0gd2luZG93LmxvY2F0aW9uO1xuICAgICAgICAgICAgICAgICAgICAgICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdmb3JtJywgbW9kYWwuYm9keSkuYXBwZW5kKG5leHRFbGVtZW50KTtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBtb2RhbC5hamF4aWZ5Rm9ybSgoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnZm9ybScsIG1vZGFsLmJvZHkpKTtcbiAgICAgICAgICAgICAgICAgICAgICAgIH0sXG4gICAgICAgICAgICAgICAgICAgICAgICBzdWNjZXNzOiBmdW5jdGlvbiAobW9kYWwsIGpzb25EYXRhKSB7XG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgd2luZG93LmxvY2F0aW9uLmhyZWYgPSBqc29uRGF0YS5yZWRpcmVjdDtcbiAgICAgICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIH0pO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgZWxzZSB7XG4gICAgICAgICAgICAgICAgLy8gaWYgbm90IG9wZW5pbmcgYSBtb2RhbCwgc3VibWl0IGEgUE9TVCByZXF1ZXN0IHRvIHRoZSBhY3Rpb24gdXJsXG4gICAgICAgICAgICAgICAgdmFyIGZvcm1FbGVtZW50ID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgnZm9ybScpO1xuICAgICAgICAgICAgICAgIGZvcm1FbGVtZW50LmFjdGlvbiA9IGJ1dHRvbkVsZW1lbnQuZGF0YXNldC53b3JrZmxvd0FjdGlvblVybDtcbiAgICAgICAgICAgICAgICBmb3JtRWxlbWVudC5tZXRob2QgPSAnUE9TVCc7XG4gICAgICAgICAgICAgICAgYWRkSGlkZGVuSW5wdXQoZm9ybUVsZW1lbnQsICdjc3JmbWlkZGxld2FyZXRva2VuJywgY3NyZlRva2VuKTtcbiAgICAgICAgICAgICAgICBhZGRIaWRkZW5JbnB1dChmb3JtRWxlbWVudCwgJ25leHQnLCB3aW5kb3cubG9jYXRpb24pO1xuICAgICAgICAgICAgICAgIGRvY3VtZW50LmJvZHkuYXBwZW5kQ2hpbGQoZm9ybUVsZW1lbnQpO1xuICAgICAgICAgICAgICAgIGZvcm1FbGVtZW50LnN1Ym1pdCgpO1xuICAgICAgICAgICAgfVxuICAgICAgICB9LCB7IGNhcHR1cmU6IHRydWUgfSk7XG4gICAgfSk7XG59XG53aW5kb3cuQWN0aXZhdGVXb3JrZmxvd0FjdGlvbnNGb3JEYXNoYm9hcmQgPVxuICAgIEFjdGl2YXRlV29ya2Zsb3dBY3Rpb25zRm9yRGFzaGJvYXJkO1xuZnVuY3Rpb24gQWN0aXZhdGVXb3JrZmxvd0FjdGlvbnNGb3JFZGl0Vmlldyhmb3JtU2VsZWN0b3IpIHtcbiAgICB2YXIgZm9ybSA9ICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKGZvcm1TZWxlY3RvcikuZ2V0KDApO1xuICAgIHZhciB3b3JrZmxvd0FjdGlvbkVsZW1lbnRzID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbCgnW2RhdGEtd29ya2Zsb3ctYWN0aW9uLW5hbWVdJyk7XG4gICAgd29ya2Zsb3dBY3Rpb25FbGVtZW50cy5mb3JFYWNoKGZ1bmN0aW9uIChidXR0b25FbGVtZW50KSB7XG4gICAgICAgIGJ1dHRvbkVsZW1lbnQuYWRkRXZlbnRMaXN0ZW5lcignY2xpY2snLCBmdW5jdGlvbiAoZSkge1xuICAgICAgICAgICAgaWYgKCd3b3JrZmxvd0FjdGlvbk1vZGFsVXJsJyBpbiBidXR0b25FbGVtZW50LmRhdGFzZXQpIHtcbiAgICAgICAgICAgICAgICAvLyBUaGlzIGFjdGlvbiByZXF1aXJlcyBvcGVuaW5nIGEgbW9kYWwgdG8gY29sbGVjdCBhZGRpdGlvbmFsIGRhdGEuXG4gICAgICAgICAgICAgICAgLy8gU3RvcCB0aGUgYnV0dG9uIGZyb20gc3VibWl0dGluZyB0aGUgZm9ybVxuICAgICAgICAgICAgICAgIGUucHJldmVudERlZmF1bHQoKTtcbiAgICAgICAgICAgICAgICBlLnN0b3BQcm9wYWdhdGlvbigpO1xuICAgICAgICAgICAgICAgIC8vIG9wZW4gdGhlIG1vZGFsIGF0IHRoZSBnaXZlbiBVUkxcbiAgICAgICAgICAgICAgICAvLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgbm8tdW5kZWZcbiAgICAgICAgICAgICAgICBNb2RhbFdvcmtmbG93KHtcbiAgICAgICAgICAgICAgICAgICAgdXJsOiBidXR0b25FbGVtZW50LmRhdGFzZXQud29ya2Zsb3dBY3Rpb25Nb2RhbFVybCxcbiAgICAgICAgICAgICAgICAgICAgb25sb2FkOiB7XG4gICAgICAgICAgICAgICAgICAgICAgICBhY3Rpb246IGZ1bmN0aW9uIChtb2RhbCkge1xuICAgICAgICAgICAgICAgICAgICAgICAgICAgIG1vZGFsLmFqYXhpZnlGb3JtKCgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdmb3JtJywgbW9kYWwuYm9keSkpO1xuICAgICAgICAgICAgICAgICAgICAgICAgfSxcbiAgICAgICAgICAgICAgICAgICAgICAgIHN1Y2Nlc3M6IGZ1bmN0aW9uIChtb2RhbCwganNvbkRhdGEpIHtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICAvLyBhIHN1Y2Nlc3MgcmVzcG9uc2UgaW5jbHVkZXMgdGhlIGFkZGl0aW9uYWwgZGF0YSB0byBzdWJtaXQgd2l0aCB0aGUgZWRpdCBmb3JtXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgYWRkSGlkZGVuSW5wdXQoZm9ybSwgJ2FjdGlvbi13b3JrZmxvdy1hY3Rpb24nLCAndHJ1ZScpO1xuICAgICAgICAgICAgICAgICAgICAgICAgICAgIGFkZEhpZGRlbklucHV0KGZvcm0sICd3b3JrZmxvdy1hY3Rpb24tbmFtZScsIGJ1dHRvbkVsZW1lbnQuZGF0YXNldC53b3JrZmxvd0FjdGlvbk5hbWUpO1xuICAgICAgICAgICAgICAgICAgICAgICAgICAgIGFkZEhpZGRlbklucHV0KGZvcm0sICd3b3JrZmxvdy1hY3Rpb24tZXh0cmEtZGF0YScsIEpTT04uc3RyaW5naWZ5KGpzb25EYXRhLmNsZWFuZWRfZGF0YSkpO1xuICAgICAgICAgICAgICAgICAgICAgICAgICAgIC8vIG5vdGU6IG5lZWQgdG8gc3VibWl0IHZpYSBqUXVlcnkgKGFzIG9wcG9zZWQgdG8gZm9ybS5zdWJtaXQoKSkgc28gdGhhdCB0aGUgb25zdWJtaXQgaGFuZGxlclxuICAgICAgICAgICAgICAgICAgICAgICAgICAgIC8vIHRoYXQgZGlzYWJsZXMgdGhlIGRpcnR5LWZvcm0gcHJvbXB0IGRvZXNuJ3QgZ2V0IGJ5cGFzc2VkXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoZm9ybSkuc3VibWl0KCk7XG4gICAgICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICB9KTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIGVsc2Uge1xuICAgICAgICAgICAgICAgIC8vIG5vIG1vZGFsLCBzbyBsZXQgdGhlIGZvcm0gc3VibWlzc2lvbiB0byB0aGUgZWRpdCB2aWV3IHByb2NlZWQsIHdpdGggYWRkaXRpb25hbFxuICAgICAgICAgICAgICAgIC8vIGhpZGRlbiBpbnB1dHMgdG8gdGVsbCBpdCB0byBwZXJmb3JtIG91ciBhY3Rpb25cbiAgICAgICAgICAgICAgICBhZGRIaWRkZW5JbnB1dChmb3JtLCAnYWN0aW9uLXdvcmtmbG93LWFjdGlvbicsICd0cnVlJyk7XG4gICAgICAgICAgICAgICAgYWRkSGlkZGVuSW5wdXQoZm9ybSwgJ3dvcmtmbG93LWFjdGlvbi1uYW1lJywgYnV0dG9uRWxlbWVudC5kYXRhc2V0LndvcmtmbG93QWN0aW9uTmFtZSk7XG4gICAgICAgICAgICB9XG4gICAgICAgIH0sIHsgY2FwdHVyZTogdHJ1ZSB9KTtcbiAgICB9KTtcbn1cbndpbmRvdy5BY3RpdmF0ZVdvcmtmbG93QWN0aW9uc0ZvckVkaXRWaWV3ID0gQWN0aXZhdGVXb3JrZmxvd0FjdGlvbnNGb3JFZGl0VmlldztcbiJdLCJuYW1lcyI6W10sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/workflow-action.js\n");

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
/******/ 			"workflow-action": 0
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
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["wagtail/admin/static/wagtailadmin/js/vendor"], () => (__webpack_require__("./client/src/entrypoints/admin/workflow-action.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;