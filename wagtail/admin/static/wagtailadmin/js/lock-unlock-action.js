/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ "./client/src/entrypoints/admin/lock-unlock-action.js":
/*!************************************************************!*\
  !*** ./client/src/entrypoints/admin/lock-unlock-action.js ***!
  \************************************************************/
/***/ (() => {

eval("/* When a lock/unlock action button is clicked, make a POST request to the relevant view */\nfunction LockUnlockAction(csrfToken, next) {\n    var actionElements = document.querySelectorAll('[data-action-lock-unlock]');\n    actionElements.forEach(function (buttonElement) {\n        buttonElement.addEventListener('click', function (e) {\n            e.stopPropagation();\n            var formElement = document.createElement('form');\n            formElement.action = buttonElement.dataset.url;\n            formElement.method = 'POST';\n            var csrftokenElement = document.createElement('input');\n            csrftokenElement.type = 'hidden';\n            csrftokenElement.name = 'csrfmiddlewaretoken';\n            csrftokenElement.value = csrfToken;\n            formElement.appendChild(csrftokenElement);\n            if (typeof next !== 'undefined') {\n                var nextElement = document.createElement('input');\n                nextElement.type = 'hidden';\n                nextElement.name = 'next';\n                nextElement.value = next;\n                formElement.appendChild(nextElement);\n            }\n            document.body.appendChild(formElement);\n            formElement.submit();\n        }, { capture: true });\n    });\n}\nwindow.LockUnlockAction = LockUnlockAction;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL2xvY2stdW5sb2NrLWFjdGlvbi5qcy5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly93YWd0YWlsLy4vY2xpZW50L3NyYy9lbnRyeXBvaW50cy9hZG1pbi9sb2NrLXVubG9jay1hY3Rpb24uanM/MGEyNyJdLCJzb3VyY2VzQ29udGVudCI6WyIvKiBXaGVuIGEgbG9jay91bmxvY2sgYWN0aW9uIGJ1dHRvbiBpcyBjbGlja2VkLCBtYWtlIGEgUE9TVCByZXF1ZXN0IHRvIHRoZSByZWxldmFudCB2aWV3ICovXG5mdW5jdGlvbiBMb2NrVW5sb2NrQWN0aW9uKGNzcmZUb2tlbiwgbmV4dCkge1xuICAgIHZhciBhY3Rpb25FbGVtZW50cyA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoJ1tkYXRhLWFjdGlvbi1sb2NrLXVubG9ja10nKTtcbiAgICBhY3Rpb25FbGVtZW50cy5mb3JFYWNoKGZ1bmN0aW9uIChidXR0b25FbGVtZW50KSB7XG4gICAgICAgIGJ1dHRvbkVsZW1lbnQuYWRkRXZlbnRMaXN0ZW5lcignY2xpY2snLCBmdW5jdGlvbiAoZSkge1xuICAgICAgICAgICAgZS5zdG9wUHJvcGFnYXRpb24oKTtcbiAgICAgICAgICAgIHZhciBmb3JtRWxlbWVudCA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoJ2Zvcm0nKTtcbiAgICAgICAgICAgIGZvcm1FbGVtZW50LmFjdGlvbiA9IGJ1dHRvbkVsZW1lbnQuZGF0YXNldC51cmw7XG4gICAgICAgICAgICBmb3JtRWxlbWVudC5tZXRob2QgPSAnUE9TVCc7XG4gICAgICAgICAgICB2YXIgY3NyZnRva2VuRWxlbWVudCA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoJ2lucHV0Jyk7XG4gICAgICAgICAgICBjc3JmdG9rZW5FbGVtZW50LnR5cGUgPSAnaGlkZGVuJztcbiAgICAgICAgICAgIGNzcmZ0b2tlbkVsZW1lbnQubmFtZSA9ICdjc3JmbWlkZGxld2FyZXRva2VuJztcbiAgICAgICAgICAgIGNzcmZ0b2tlbkVsZW1lbnQudmFsdWUgPSBjc3JmVG9rZW47XG4gICAgICAgICAgICBmb3JtRWxlbWVudC5hcHBlbmRDaGlsZChjc3JmdG9rZW5FbGVtZW50KTtcbiAgICAgICAgICAgIGlmICh0eXBlb2YgbmV4dCAhPT0gJ3VuZGVmaW5lZCcpIHtcbiAgICAgICAgICAgICAgICB2YXIgbmV4dEVsZW1lbnQgPSBkb2N1bWVudC5jcmVhdGVFbGVtZW50KCdpbnB1dCcpO1xuICAgICAgICAgICAgICAgIG5leHRFbGVtZW50LnR5cGUgPSAnaGlkZGVuJztcbiAgICAgICAgICAgICAgICBuZXh0RWxlbWVudC5uYW1lID0gJ25leHQnO1xuICAgICAgICAgICAgICAgIG5leHRFbGVtZW50LnZhbHVlID0gbmV4dDtcbiAgICAgICAgICAgICAgICBmb3JtRWxlbWVudC5hcHBlbmRDaGlsZChuZXh0RWxlbWVudCk7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBkb2N1bWVudC5ib2R5LmFwcGVuZENoaWxkKGZvcm1FbGVtZW50KTtcbiAgICAgICAgICAgIGZvcm1FbGVtZW50LnN1Ym1pdCgpO1xuICAgICAgICB9LCB7IGNhcHR1cmU6IHRydWUgfSk7XG4gICAgfSk7XG59XG53aW5kb3cuTG9ja1VubG9ja0FjdGlvbiA9IExvY2tVbmxvY2tBY3Rpb247XG4iXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/lock-unlock-action.js\n");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval-source-map devtool is used.
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./client/src/entrypoints/admin/lock-unlock-action.js"]();
/******/ 	
/******/ })()
;