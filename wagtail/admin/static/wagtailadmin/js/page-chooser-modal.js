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

/***/ "./client/src/entrypoints/admin/page-chooser-modal.js":
/*!************************************************************!*\
  !*** ./client/src/entrypoints/admin/page-chooser-modal.js ***!
  \************************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

eval("\nvar __importDefault = (this && this.__importDefault) || function (mod) {\n    return (mod && mod.__esModule) ? mod : { \"default\": mod };\n};\nexports.__esModule = true;\nvar jquery_1 = __importDefault(__webpack_require__(/*! jquery */ \"jquery\"));\nvar initTooltips_1 = __webpack_require__(/*! ../../includes/initTooltips */ \"./client/src/includes/initTooltips.ts\");\n/* global wagtail */\nvar PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS = {\n    browse: function (modal, jsonData) {\n        /* Set up link-types links to open in the modal */\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('.link-types a', modal.body).on('click', function () {\n            modal.loadUrl(this.href);\n            return false;\n        });\n        /* Initialize dropdowns */\n        wagtail.ui.initDropDowns();\n        /* Set up dropdown links to open in the modal */\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('.c-dropdown__item .u-link', modal.body).on('click', function () {\n            modal.loadUrl(this.href);\n            return false;\n        });\n        /* Set up submissions of the search form to open in the modal. */\n        modal.ajaxifyForm((0, jquery_1[\"default\"])('form.search-form', modal.body));\n        /* Set up search-as-you-type behaviour on the search box */\n        var searchUrl = (0, jquery_1[\"default\"])('form.search-form', modal.body).attr('action');\n        /* save initial page browser HTML, so that we can restore it if the search box gets cleared */\n        var initialPageResultsHtml = (0, jquery_1[\"default\"])('.page-results', modal.body).html();\n        var request;\n        function search() {\n            var query = (0, jquery_1[\"default\"])('#id_q', modal.body).val();\n            if (query !== '') {\n                request = jquery_1[\"default\"].ajax({\n                    url: searchUrl,\n                    data: {\n                        // eslint-disable-next-line id-length\n                        q: query\n                    },\n                    success: function (data) {\n                        request = null;\n                        (0, jquery_1[\"default\"])('.page-results', modal.body).html(data);\n                        // eslint-disable-next-line @typescript-eslint/no-use-before-define\n                        ajaxifySearchResults();\n                    },\n                    error: function () {\n                        request = null;\n                    }\n                });\n            }\n            else {\n                /* search box is empty - restore original page browser HTML */\n                (0, jquery_1[\"default\"])('.page-results', modal.body).html(initialPageResultsHtml);\n                // eslint-disable-next-line @typescript-eslint/no-use-before-define\n                ajaxifyBrowseResults();\n            }\n            return false;\n        }\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('#id_q', modal.body).on('input', function () {\n            if (request) {\n                request.abort();\n            }\n            clearTimeout(jquery_1[\"default\"].data(this, 'timer'));\n            var wait = setTimeout(search, 200);\n            (0, jquery_1[\"default\"])(this).data('timer', wait);\n        });\n        /* Set up behaviour of choose-page links in the newly-loaded search results,\n        to pass control back to the calling page */\n        function ajaxifySearchResults() {\n            // eslint-disable-next-line func-names\n            (0, jquery_1[\"default\"])('.page-results a.choose-page', modal.body).on('click', function () {\n                var pageData = (0, jquery_1[\"default\"])(this).data();\n                modal.respond('pageChosen', pageData);\n                modal.close();\n                return false;\n            });\n            /* pagination links within search results should be AJAX-fetched\n            and the result loaded into .page-results (and ajaxified) */\n            (0, jquery_1[\"default\"])('.page-results a.navigate-pages, .page-results [data-breadcrumb-item] a', modal.body).on('click', function handleLinkClick() {\n                (0, jquery_1[\"default\"])('.page-results', modal.body).load(this.href, ajaxifySearchResults);\n                return false;\n            });\n            /* Set up parent navigation links (.navigate-parent) to open in the modal */\n            // eslint-disable-next-line func-names\n            (0, jquery_1[\"default\"])('.page-results a.navigate-parent', modal.body).on('click', function () {\n                modal.loadUrl(this.href);\n                return false;\n            });\n        }\n        function ajaxifyBrowseResults() {\n            /* Set up page navigation links to open in the modal */\n            (0, jquery_1[\"default\"])('.page-results a.navigate-pages, .page-results [data-breadcrumb-item] a', modal.body).on('click', function handleLinkClick() {\n                modal.loadUrl(this.href);\n                return false;\n            });\n            /* Set up behaviour of choose-page links, to pass control back to the calling page */\n            // eslint-disable-next-line func-names\n            (0, jquery_1[\"default\"])('a.choose-page', modal.body).on('click', function () {\n                var pageData = (0, jquery_1[\"default\"])(this).data();\n                pageData.parentId = jsonData.parent_page_id;\n                modal.respond('pageChosen', pageData);\n                modal.close();\n                return false;\n            });\n            // eslint-disable-next-line func-names\n            (0, jquery_1[\"default\"])('.c-dropdown__item .u-link', modal.body).on('click', function () {\n                modal.loadUrl(this.href);\n                return false;\n            });\n            wagtail.ui.initDropDowns();\n        }\n        ajaxifyBrowseResults();\n        (0, initTooltips_1.initTooltips)();\n        /*\n        Focus on the search box when opening the modal.\n        FIXME: this doesn't seem to have any effect (at least on Chrome)\n        */\n        (0, jquery_1[\"default\"])('#id_q', modal.body).trigger('focus');\n    },\n    anchor_link: function (modal) {\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('p.link-types a', modal.body).on('click', function () {\n            modal.loadUrl(this.href);\n            return false;\n        });\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('form', modal.body).on('submit', function () {\n            modal.postForm(this.action, (0, jquery_1[\"default\"])(this).serialize());\n            return false;\n        });\n    },\n    email_link: function (modal) {\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('p.link-types a', modal.body).on('click', function () {\n            modal.loadUrl(this.href);\n            return false;\n        });\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('form', modal.body).on('submit', function () {\n            modal.postForm(this.action, (0, jquery_1[\"default\"])(this).serialize());\n            return false;\n        });\n    },\n    phone_link: function (modal) {\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('p.link-types a', modal.body).on('click', function () {\n            modal.loadUrl(this.href);\n            return false;\n        });\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('form', modal.body).on('submit', function () {\n            modal.postForm(this.action, (0, jquery_1[\"default\"])(this).serialize());\n            return false;\n        });\n    },\n    external_link: function (modal) {\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('p.link-types a', modal.body).on('click', function () {\n            modal.loadUrl(this.href);\n            return false;\n        });\n        // eslint-disable-next-line func-names\n        (0, jquery_1[\"default\"])('form', modal.body).on('submit', function () {\n            modal.postForm(this.action, (0, jquery_1[\"default\"])(this).serialize());\n            return false;\n        });\n    },\n    external_link_chosen: function (modal, jsonData) {\n        modal.respond('pageChosen', jsonData.result);\n        modal.close();\n    },\n    confirm_external_to_internal: function (modal, jsonData) {\n        // eslint-disable-next-line func-names, prefer-arrow-callback\n        (0, jquery_1[\"default\"])('[data-action-confirm]', modal.body).on('click', function () {\n            modal.respond('pageChosen', jsonData.internal);\n            modal.close();\n            return false;\n        });\n        // eslint-disable-next-line func-names, prefer-arrow-callback\n        (0, jquery_1[\"default\"])('[data-action-deny]', modal.body).on('click', function () {\n            modal.respond('pageChosen', jsonData.external);\n            modal.close();\n            return false;\n        });\n    }\n};\nwindow.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS = PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL3BhZ2UtY2hvb3Nlci1tb2RhbC5qcy5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly93YWd0YWlsLy4vY2xpZW50L3NyYy9lbnRyeXBvaW50cy9hZG1pbi9wYWdlLWNob29zZXItbW9kYWwuanM/Zjg4YyJdLCJzb3VyY2VzQ29udGVudCI6WyJcInVzZSBzdHJpY3RcIjtcbnZhciBfX2ltcG9ydERlZmF1bHQgPSAodGhpcyAmJiB0aGlzLl9faW1wb3J0RGVmYXVsdCkgfHwgZnVuY3Rpb24gKG1vZCkge1xuICAgIHJldHVybiAobW9kICYmIG1vZC5fX2VzTW9kdWxlKSA/IG1vZCA6IHsgXCJkZWZhdWx0XCI6IG1vZCB9O1xufTtcbmV4cG9ydHMuX19lc01vZHVsZSA9IHRydWU7XG52YXIganF1ZXJ5XzEgPSBfX2ltcG9ydERlZmF1bHQocmVxdWlyZShcImpxdWVyeVwiKSk7XG52YXIgaW5pdFRvb2x0aXBzXzEgPSByZXF1aXJlKFwiLi4vLi4vaW5jbHVkZXMvaW5pdFRvb2x0aXBzXCIpO1xuLyogZ2xvYmFsIHdhZ3RhaWwgKi9cbnZhciBQQUdFX0NIT09TRVJfTU9EQUxfT05MT0FEX0hBTkRMRVJTID0ge1xuICAgIGJyb3dzZTogZnVuY3Rpb24gKG1vZGFsLCBqc29uRGF0YSkge1xuICAgICAgICAvKiBTZXQgdXAgbGluay10eXBlcyBsaW5rcyB0byBvcGVuIGluIHRoZSBtb2RhbCAqL1xuICAgICAgICAvLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgZnVuYy1uYW1lc1xuICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnLmxpbmstdHlwZXMgYScsIG1vZGFsLmJvZHkpLm9uKCdjbGljaycsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIG1vZGFsLmxvYWRVcmwodGhpcy5ocmVmKTtcbiAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgfSk7XG4gICAgICAgIC8qIEluaXRpYWxpemUgZHJvcGRvd25zICovXG4gICAgICAgIHdhZ3RhaWwudWkuaW5pdERyb3BEb3ducygpO1xuICAgICAgICAvKiBTZXQgdXAgZHJvcGRvd24gbGlua3MgdG8gb3BlbiBpbiB0aGUgbW9kYWwgKi9cbiAgICAgICAgLy8gZXNsaW50LWRpc2FibGUtbmV4dC1saW5lIGZ1bmMtbmFtZXNcbiAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJy5jLWRyb3Bkb3duX19pdGVtIC51LWxpbmsnLCBtb2RhbC5ib2R5KS5vbignY2xpY2snLCBmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICBtb2RhbC5sb2FkVXJsKHRoaXMuaHJlZik7XG4gICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgIH0pO1xuICAgICAgICAvKiBTZXQgdXAgc3VibWlzc2lvbnMgb2YgdGhlIHNlYXJjaCBmb3JtIHRvIG9wZW4gaW4gdGhlIG1vZGFsLiAqL1xuICAgICAgICBtb2RhbC5hamF4aWZ5Rm9ybSgoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnZm9ybS5zZWFyY2gtZm9ybScsIG1vZGFsLmJvZHkpKTtcbiAgICAgICAgLyogU2V0IHVwIHNlYXJjaC1hcy15b3UtdHlwZSBiZWhhdmlvdXIgb24gdGhlIHNlYXJjaCBib3ggKi9cbiAgICAgICAgdmFyIHNlYXJjaFVybCA9ICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdmb3JtLnNlYXJjaC1mb3JtJywgbW9kYWwuYm9keSkuYXR0cignYWN0aW9uJyk7XG4gICAgICAgIC8qIHNhdmUgaW5pdGlhbCBwYWdlIGJyb3dzZXIgSFRNTCwgc28gdGhhdCB3ZSBjYW4gcmVzdG9yZSBpdCBpZiB0aGUgc2VhcmNoIGJveCBnZXRzIGNsZWFyZWQgKi9cbiAgICAgICAgdmFyIGluaXRpYWxQYWdlUmVzdWx0c0h0bWwgPSAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnLnBhZ2UtcmVzdWx0cycsIG1vZGFsLmJvZHkpLmh0bWwoKTtcbiAgICAgICAgdmFyIHJlcXVlc3Q7XG4gICAgICAgIGZ1bmN0aW9uIHNlYXJjaCgpIHtcbiAgICAgICAgICAgIHZhciBxdWVyeSA9ICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCcjaWRfcScsIG1vZGFsLmJvZHkpLnZhbCgpO1xuICAgICAgICAgICAgaWYgKHF1ZXJ5ICE9PSAnJykge1xuICAgICAgICAgICAgICAgIHJlcXVlc3QgPSBqcXVlcnlfMVtcImRlZmF1bHRcIl0uYWpheCh7XG4gICAgICAgICAgICAgICAgICAgIHVybDogc2VhcmNoVXJsLFxuICAgICAgICAgICAgICAgICAgICBkYXRhOiB7XG4gICAgICAgICAgICAgICAgICAgICAgICAvLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgaWQtbGVuZ3RoXG4gICAgICAgICAgICAgICAgICAgICAgICBxOiBxdWVyeVxuICAgICAgICAgICAgICAgICAgICB9LFxuICAgICAgICAgICAgICAgICAgICBzdWNjZXNzOiBmdW5jdGlvbiAoZGF0YSkge1xuICAgICAgICAgICAgICAgICAgICAgICAgcmVxdWVzdCA9IG51bGw7XG4gICAgICAgICAgICAgICAgICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnLnBhZ2UtcmVzdWx0cycsIG1vZGFsLmJvZHkpLmh0bWwoZGF0YSk7XG4gICAgICAgICAgICAgICAgICAgICAgICAvLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgQHR5cGVzY3JpcHQtZXNsaW50L25vLXVzZS1iZWZvcmUtZGVmaW5lXG4gICAgICAgICAgICAgICAgICAgICAgICBhamF4aWZ5U2VhcmNoUmVzdWx0cygpO1xuICAgICAgICAgICAgICAgICAgICB9LFxuICAgICAgICAgICAgICAgICAgICBlcnJvcjogZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgICAgICAgICAgICAgcmVxdWVzdCA9IG51bGw7XG4gICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICB9KTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIGVsc2Uge1xuICAgICAgICAgICAgICAgIC8qIHNlYXJjaCBib3ggaXMgZW1wdHkgLSByZXN0b3JlIG9yaWdpbmFsIHBhZ2UgYnJvd3NlciBIVE1MICovXG4gICAgICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJy5wYWdlLXJlc3VsdHMnLCBtb2RhbC5ib2R5KS5odG1sKGluaXRpYWxQYWdlUmVzdWx0c0h0bWwpO1xuICAgICAgICAgICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBAdHlwZXNjcmlwdC1lc2xpbnQvbm8tdXNlLWJlZm9yZS1kZWZpbmVcbiAgICAgICAgICAgICAgICBhamF4aWZ5QnJvd3NlUmVzdWx0cygpO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICB9XG4gICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCcjaWRfcScsIG1vZGFsLmJvZHkpLm9uKCdpbnB1dCcsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIGlmIChyZXF1ZXN0KSB7XG4gICAgICAgICAgICAgICAgcmVxdWVzdC5hYm9ydCgpO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgY2xlYXJUaW1lb3V0KGpxdWVyeV8xW1wiZGVmYXVsdFwiXS5kYXRhKHRoaXMsICd0aW1lcicpKTtcbiAgICAgICAgICAgIHZhciB3YWl0ID0gc2V0VGltZW91dChzZWFyY2gsIDIwMCk7XG4gICAgICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSh0aGlzKS5kYXRhKCd0aW1lcicsIHdhaXQpO1xuICAgICAgICB9KTtcbiAgICAgICAgLyogU2V0IHVwIGJlaGF2aW91ciBvZiBjaG9vc2UtcGFnZSBsaW5rcyBpbiB0aGUgbmV3bHktbG9hZGVkIHNlYXJjaCByZXN1bHRzLFxuICAgICAgICB0byBwYXNzIGNvbnRyb2wgYmFjayB0byB0aGUgY2FsbGluZyBwYWdlICovXG4gICAgICAgIGZ1bmN0aW9uIGFqYXhpZnlTZWFyY2hSZXN1bHRzKCkge1xuICAgICAgICAgICAgLy8gZXNsaW50LWRpc2FibGUtbmV4dC1saW5lIGZ1bmMtbmFtZXNcbiAgICAgICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCcucGFnZS1yZXN1bHRzIGEuY2hvb3NlLXBhZ2UnLCBtb2RhbC5ib2R5KS5vbignY2xpY2snLCBmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICAgICAgdmFyIHBhZ2VEYXRhID0gKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkodGhpcykuZGF0YSgpO1xuICAgICAgICAgICAgICAgIG1vZGFsLnJlc3BvbmQoJ3BhZ2VDaG9zZW4nLCBwYWdlRGF0YSk7XG4gICAgICAgICAgICAgICAgbW9kYWwuY2xvc2UoKTtcbiAgICAgICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgICAgICB9KTtcbiAgICAgICAgICAgIC8qIHBhZ2luYXRpb24gbGlua3Mgd2l0aGluIHNlYXJjaCByZXN1bHRzIHNob3VsZCBiZSBBSkFYLWZldGNoZWRcbiAgICAgICAgICAgIGFuZCB0aGUgcmVzdWx0IGxvYWRlZCBpbnRvIC5wYWdlLXJlc3VsdHMgKGFuZCBhamF4aWZpZWQpICovXG4gICAgICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnLnBhZ2UtcmVzdWx0cyBhLm5hdmlnYXRlLXBhZ2VzLCAucGFnZS1yZXN1bHRzIFtkYXRhLWJyZWFkY3J1bWItaXRlbV0gYScsIG1vZGFsLmJvZHkpLm9uKCdjbGljaycsIGZ1bmN0aW9uIGhhbmRsZUxpbmtDbGljaygpIHtcbiAgICAgICAgICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnLnBhZ2UtcmVzdWx0cycsIG1vZGFsLmJvZHkpLmxvYWQodGhpcy5ocmVmLCBhamF4aWZ5U2VhcmNoUmVzdWx0cyk7XG4gICAgICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgICAgfSk7XG4gICAgICAgICAgICAvKiBTZXQgdXAgcGFyZW50IG5hdmlnYXRpb24gbGlua3MgKC5uYXZpZ2F0ZS1wYXJlbnQpIHRvIG9wZW4gaW4gdGhlIG1vZGFsICovXG4gICAgICAgICAgICAvLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgZnVuYy1uYW1lc1xuICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJy5wYWdlLXJlc3VsdHMgYS5uYXZpZ2F0ZS1wYXJlbnQnLCBtb2RhbC5ib2R5KS5vbignY2xpY2snLCBmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICAgICAgbW9kYWwubG9hZFVybCh0aGlzLmhyZWYpO1xuICAgICAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgICAgIH0pO1xuICAgICAgICB9XG4gICAgICAgIGZ1bmN0aW9uIGFqYXhpZnlCcm93c2VSZXN1bHRzKCkge1xuICAgICAgICAgICAgLyogU2V0IHVwIHBhZ2UgbmF2aWdhdGlvbiBsaW5rcyB0byBvcGVuIGluIHRoZSBtb2RhbCAqL1xuICAgICAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJy5wYWdlLXJlc3VsdHMgYS5uYXZpZ2F0ZS1wYWdlcywgLnBhZ2UtcmVzdWx0cyBbZGF0YS1icmVhZGNydW1iLWl0ZW1dIGEnLCBtb2RhbC5ib2R5KS5vbignY2xpY2snLCBmdW5jdGlvbiBoYW5kbGVMaW5rQ2xpY2soKSB7XG4gICAgICAgICAgICAgICAgbW9kYWwubG9hZFVybCh0aGlzLmhyZWYpO1xuICAgICAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgICAgIH0pO1xuICAgICAgICAgICAgLyogU2V0IHVwIGJlaGF2aW91ciBvZiBjaG9vc2UtcGFnZSBsaW5rcywgdG8gcGFzcyBjb250cm9sIGJhY2sgdG8gdGhlIGNhbGxpbmcgcGFnZSAqL1xuICAgICAgICAgICAgLy8gZXNsaW50LWRpc2FibGUtbmV4dC1saW5lIGZ1bmMtbmFtZXNcbiAgICAgICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdhLmNob29zZS1wYWdlJywgbW9kYWwuYm9keSkub24oJ2NsaWNrJywgZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgICAgIHZhciBwYWdlRGF0YSA9ICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKHRoaXMpLmRhdGEoKTtcbiAgICAgICAgICAgICAgICBwYWdlRGF0YS5wYXJlbnRJZCA9IGpzb25EYXRhLnBhcmVudF9wYWdlX2lkO1xuICAgICAgICAgICAgICAgIG1vZGFsLnJlc3BvbmQoJ3BhZ2VDaG9zZW4nLCBwYWdlRGF0YSk7XG4gICAgICAgICAgICAgICAgbW9kYWwuY2xvc2UoKTtcbiAgICAgICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgICAgICB9KTtcbiAgICAgICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnLmMtZHJvcGRvd25fX2l0ZW0gLnUtbGluaycsIG1vZGFsLmJvZHkpLm9uKCdjbGljaycsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgICAgICBtb2RhbC5sb2FkVXJsKHRoaXMuaHJlZik7XG4gICAgICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICAgICAgfSk7XG4gICAgICAgICAgICB3YWd0YWlsLnVpLmluaXREcm9wRG93bnMoKTtcbiAgICAgICAgfVxuICAgICAgICBhamF4aWZ5QnJvd3NlUmVzdWx0cygpO1xuICAgICAgICAoMCwgaW5pdFRvb2x0aXBzXzEuaW5pdFRvb2x0aXBzKSgpO1xuICAgICAgICAvKlxuICAgICAgICBGb2N1cyBvbiB0aGUgc2VhcmNoIGJveCB3aGVuIG9wZW5pbmcgdGhlIG1vZGFsLlxuICAgICAgICBGSVhNRTogdGhpcyBkb2Vzbid0IHNlZW0gdG8gaGF2ZSBhbnkgZWZmZWN0IChhdCBsZWFzdCBvbiBDaHJvbWUpXG4gICAgICAgICovXG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCcjaWRfcScsIG1vZGFsLmJvZHkpLnRyaWdnZXIoJ2ZvY3VzJyk7XG4gICAgfSxcbiAgICBhbmNob3JfbGluazogZnVuY3Rpb24gKG1vZGFsKSB7XG4gICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdwLmxpbmstdHlwZXMgYScsIG1vZGFsLmJvZHkpLm9uKCdjbGljaycsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIG1vZGFsLmxvYWRVcmwodGhpcy5ocmVmKTtcbiAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgfSk7XG4gICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdmb3JtJywgbW9kYWwuYm9keSkub24oJ3N1Ym1pdCcsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIG1vZGFsLnBvc3RGb3JtKHRoaXMuYWN0aW9uLCAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSh0aGlzKS5zZXJpYWxpemUoKSk7XG4gICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgIH0pO1xuICAgIH0sXG4gICAgZW1haWxfbGluazogZnVuY3Rpb24gKG1vZGFsKSB7XG4gICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdwLmxpbmstdHlwZXMgYScsIG1vZGFsLmJvZHkpLm9uKCdjbGljaycsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIG1vZGFsLmxvYWRVcmwodGhpcy5ocmVmKTtcbiAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgfSk7XG4gICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdmb3JtJywgbW9kYWwuYm9keSkub24oJ3N1Ym1pdCcsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIG1vZGFsLnBvc3RGb3JtKHRoaXMuYWN0aW9uLCAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSh0aGlzKS5zZXJpYWxpemUoKSk7XG4gICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgIH0pO1xuICAgIH0sXG4gICAgcGhvbmVfbGluazogZnVuY3Rpb24gKG1vZGFsKSB7XG4gICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdwLmxpbmstdHlwZXMgYScsIG1vZGFsLmJvZHkpLm9uKCdjbGljaycsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIG1vZGFsLmxvYWRVcmwodGhpcy5ocmVmKTtcbiAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgfSk7XG4gICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdmb3JtJywgbW9kYWwuYm9keSkub24oJ3N1Ym1pdCcsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIG1vZGFsLnBvc3RGb3JtKHRoaXMuYWN0aW9uLCAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSh0aGlzKS5zZXJpYWxpemUoKSk7XG4gICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgIH0pO1xuICAgIH0sXG4gICAgZXh0ZXJuYWxfbGluazogZnVuY3Rpb24gKG1vZGFsKSB7XG4gICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdwLmxpbmstdHlwZXMgYScsIG1vZGFsLmJvZHkpLm9uKCdjbGljaycsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIG1vZGFsLmxvYWRVcmwodGhpcy5ocmVmKTtcbiAgICAgICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgICAgfSk7XG4gICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzXG4gICAgICAgICgwLCBqcXVlcnlfMVtcImRlZmF1bHRcIl0pKCdmb3JtJywgbW9kYWwuYm9keSkub24oJ3N1Ym1pdCcsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIG1vZGFsLnBvc3RGb3JtKHRoaXMuYWN0aW9uLCAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSh0aGlzKS5zZXJpYWxpemUoKSk7XG4gICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgIH0pO1xuICAgIH0sXG4gICAgZXh0ZXJuYWxfbGlua19jaG9zZW46IGZ1bmN0aW9uIChtb2RhbCwganNvbkRhdGEpIHtcbiAgICAgICAgbW9kYWwucmVzcG9uZCgncGFnZUNob3NlbicsIGpzb25EYXRhLnJlc3VsdCk7XG4gICAgICAgIG1vZGFsLmNsb3NlKCk7XG4gICAgfSxcbiAgICBjb25maXJtX2V4dGVybmFsX3RvX2ludGVybmFsOiBmdW5jdGlvbiAobW9kYWwsIGpzb25EYXRhKSB7XG4gICAgICAgIC8vIGVzbGludC1kaXNhYmxlLW5leHQtbGluZSBmdW5jLW5hbWVzLCBwcmVmZXItYXJyb3ctY2FsbGJhY2tcbiAgICAgICAgKDAsIGpxdWVyeV8xW1wiZGVmYXVsdFwiXSkoJ1tkYXRhLWFjdGlvbi1jb25maXJtXScsIG1vZGFsLmJvZHkpLm9uKCdjbGljaycsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIG1vZGFsLnJlc3BvbmQoJ3BhZ2VDaG9zZW4nLCBqc29uRGF0YS5pbnRlcm5hbCk7XG4gICAgICAgICAgICBtb2RhbC5jbG9zZSgpO1xuICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICB9KTtcbiAgICAgICAgLy8gZXNsaW50LWRpc2FibGUtbmV4dC1saW5lIGZ1bmMtbmFtZXMsIHByZWZlci1hcnJvdy1jYWxsYmFja1xuICAgICAgICAoMCwganF1ZXJ5XzFbXCJkZWZhdWx0XCJdKSgnW2RhdGEtYWN0aW9uLWRlbnldJywgbW9kYWwuYm9keSkub24oJ2NsaWNrJywgZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgbW9kYWwucmVzcG9uZCgncGFnZUNob3NlbicsIGpzb25EYXRhLmV4dGVybmFsKTtcbiAgICAgICAgICAgIG1vZGFsLmNsb3NlKCk7XG4gICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgIH0pO1xuICAgIH1cbn07XG53aW5kb3cuUEFHRV9DSE9PU0VSX01PREFMX09OTE9BRF9IQU5ETEVSUyA9IFBBR0VfQ0hPT1NFUl9NT0RBTF9PTkxPQURfSEFORExFUlM7XG4iXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/page-chooser-modal.js\n");

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
/******/ 			"page-chooser-modal": 0
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
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["wagtail/admin/static/wagtailadmin/js/vendor"], () => (__webpack_require__("./client/src/entrypoints/admin/page-chooser-modal.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;