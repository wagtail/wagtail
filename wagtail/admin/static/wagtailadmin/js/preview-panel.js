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

/***/ "./client/src/entrypoints/admin/preview-panel.js":
/*!*******************************************************!*\
  !*** ./client/src/entrypoints/admin/preview-panel.js ***!
  \*******************************************************/
/***/ ((__unused_webpack_module, exports, __webpack_require__) => {

eval("\nexports.__esModule = true;\nvar wagtailConfig_1 = __webpack_require__(/*! ../../config/wagtailConfig */ \"./client/src/config/wagtailConfig.js\");\nvar gettext_1 = __webpack_require__(/*! ../../utils/gettext */ \"./client/src/utils/gettext.ts\");\nfunction initPreview() {\n    var previewSidePanel = document.querySelector('[data-side-panel=\"preview\"]');\n    // Preview side panel is not shown if the object does not have any preview modes\n    if (!previewSidePanel)\n        return;\n    // The previewSidePanel is a generic container for side panels,\n    // the content of the preview panel itself is in a child element\n    var previewPanel = previewSidePanel.querySelector('[data-preview-panel]');\n    //\n    // Preview size handling\n    //\n    var sizeInputs = previewPanel.querySelectorAll('[data-device-width]');\n    var defaultSizeInput = previewPanel.querySelector('[data-default-size]');\n    var setPreviewWidth = function (width) {\n        var isUnavailable = previewPanel.classList.contains('preview-panel--unavailable');\n        var deviceWidth = width;\n        // Reset to default size if width is falsy or preview is unavailable\n        if (!width || isUnavailable) {\n            deviceWidth = defaultSizeInput.dataset.deviceWidth;\n        }\n        previewPanel.style.setProperty('--preview-device-width', deviceWidth);\n    };\n    var togglePreviewSize = function (event) {\n        var device = event.target.value;\n        var deviceWidth = event.target.dataset.deviceWidth;\n        setPreviewWidth(deviceWidth);\n        try {\n            localStorage.setItem('wagtail:preview-panel-device', device);\n        }\n        catch (e) {\n            // Skip saving the device if localStorage fails.\n        }\n        // Ensure only one device class is applied\n        sizeInputs.forEach(function (input) {\n            previewPanel.classList.toggle(\"preview-panel--\".concat(input.value), input.value === device);\n        });\n    };\n    sizeInputs.forEach(function (input) {\n        return input.addEventListener('change', togglePreviewSize);\n    });\n    var resizeObserver = new ResizeObserver(function (entries) {\n        return previewPanel.style.setProperty('--preview-panel-width', entries[0].contentRect.width);\n    });\n    resizeObserver.observe(previewPanel);\n    //\n    // Preview data handling\n    //\n    // In order to make the preview truly reliable, the preview page needs\n    // to be perfectly independent from the edit page,\n    // from the browser perspective. To pass data from the edit page\n    // to the preview page, we send the form after each change\n    // and save it inside the user session.\n    var newTabButton = previewPanel.querySelector('[data-preview-new-tab]');\n    var refreshButton = previewPanel.querySelector('[data-refresh-preview]');\n    var loadingSpinner = previewPanel.querySelector('[data-preview-spinner]');\n    var form = document.querySelector('[data-edit-form]');\n    var previewUrl = previewPanel.dataset.action;\n    var previewModeSelect = document.querySelector('[data-preview-mode-select]');\n    var iframe = previewPanel.querySelector('[data-preview-iframe]');\n    var spinnerTimeout;\n    var hasPendingUpdate = false;\n    var finishUpdate = function () {\n        clearTimeout(spinnerTimeout);\n        loadingSpinner.classList.add('w-hidden');\n        hasPendingUpdate = false;\n    };\n    var reloadIframe = function () {\n        // Instead of reloading the iframe, we're replacing it with a new iframe to\n        // prevent flashing\n        // Create a new invisible iframe element\n        var newIframe = document.createElement('iframe');\n        newIframe.style.width = 0;\n        newIframe.style.height = 0;\n        newIframe.style.opacity = 0;\n        newIframe.style.position = 'absolute';\n        newIframe.src = iframe.src;\n        // Put it in the DOM so it loads the page\n        iframe.insertAdjacentElement('afterend', newIframe);\n        var handleLoad = function () {\n            // Copy all attributes from the old iframe to the new one,\n            // except src as that will cause the iframe to be reloaded\n            Array.from(iframe.attributes).forEach(function (key) {\n                if (key.nodeName === 'src')\n                    return;\n                newIframe.setAttribute(key.nodeName, key.nodeValue);\n            });\n            // Restore scroll position\n            newIframe.contentWindow.scroll(iframe.contentWindow.scrollX, iframe.contentWindow.scrollY);\n            // Remove the old iframe and swap it with the new one\n            iframe.remove();\n            iframe = newIframe;\n            // Make the new iframe visible\n            newIframe.style = null;\n            // Ready for another update\n            finishUpdate();\n            // Remove the load event listener so it doesn't fire when switching modes\n            newIframe.removeEventListener('load', handleLoad);\n        };\n        newIframe.addEventListener('load', handleLoad);\n    };\n    var clearPreviewData = function () {\n        var _a;\n        return fetch(previewUrl, {\n            headers: (_a = {}, _a[wagtailConfig_1.WAGTAIL_CONFIG.CSRF_HEADER_NAME] = wagtailConfig_1.WAGTAIL_CONFIG.CSRF_TOKEN, _a),\n            method: 'DELETE'\n        });\n    };\n    var setPreviewData = function () {\n        // Bail out if there is already a pending update\n        if (hasPendingUpdate)\n            return Promise.resolve();\n        hasPendingUpdate = true;\n        spinnerTimeout = setTimeout(function () { return loadingSpinner.classList.remove('w-hidden'); }, 2000);\n        return fetch(previewUrl, {\n            method: 'POST',\n            body: new FormData(form)\n        })\n            .then(function (response) { return response.json(); })\n            .then(function (data) {\n            previewPanel.classList.toggle('preview-panel--has-errors', !data.is_valid);\n            previewPanel.classList.toggle('preview-panel--unavailable', !data.is_available);\n            if (data.is_valid) {\n                reloadIframe();\n            }\n            else {\n                finishUpdate();\n            }\n            return data.is_valid;\n        })[\"catch\"](function (error) {\n            finishUpdate();\n            // Re-throw error so it can be handled by handlePreview\n            throw error;\n        });\n    };\n    var handlePreview = function () {\n        return setPreviewData()[\"catch\"](function () {\n            // eslint-disable-next-line no-alert\n            window.alert((0, gettext_1.gettext)('Error while sending preview data.'));\n        });\n    };\n    var handlePreviewInNewTab = function (event) {\n        event.preventDefault();\n        var previewWindow = window.open('', previewUrl);\n        previewWindow.focus();\n        handlePreview().then(function (success) {\n            if (success) {\n                var url = new URL(newTabButton.href);\n                previewWindow.document.location = url.toString();\n            }\n            else {\n                window.focus();\n                previewWindow.close();\n            }\n        });\n    };\n    newTabButton.addEventListener('click', handlePreviewInNewTab);\n    if (refreshButton) {\n        refreshButton.addEventListener('click', handlePreview);\n    }\n    if (wagtailConfig_1.WAGTAIL_CONFIG.WAGTAIL_AUTO_UPDATE_PREVIEW) {\n        var oldPayload_1 = new URLSearchParams(new FormData(form)).toString();\n        var updateInterval_1;\n        var hasChanges_1 = function () {\n            var newPayload = new URLSearchParams(new FormData(form)).toString();\n            var changed = oldPayload_1 !== newPayload;\n            oldPayload_1 = newPayload;\n            return changed;\n        };\n        var checkAndUpdatePreview_1 = function () {\n            // Do not check for preview update if an update request is still pending\n            // and don't send a new request if the form hasn't changed\n            if (hasPendingUpdate || !hasChanges_1())\n                return;\n            setPreviewData();\n        };\n        previewSidePanel.addEventListener('show', function () {\n            // Immediately update the preview when the panel is opened\n            checkAndUpdatePreview_1();\n            // Only set the interval while the panel is shown\n            updateInterval_1 = setInterval(checkAndUpdatePreview_1, wagtailConfig_1.WAGTAIL_CONFIG.WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL);\n        });\n        previewSidePanel.addEventListener('hide', function () {\n            clearInterval(updateInterval_1);\n        });\n    }\n    //\n    // Preview mode handling\n    //\n    var handlePreviewModeChange = function (event) {\n        var mode = event.target.value;\n        var url = new URL(iframe.src);\n        url.searchParams.set('mode', mode);\n        iframe.src = url.toString();\n        url.searchParams[\"delete\"]('in_preview_panel');\n        newTabButton.href = url.toString();\n        // Make sure data is updated\n        handlePreview();\n    };\n    if (previewModeSelect) {\n        previewModeSelect.addEventListener('change', handlePreviewModeChange);\n    }\n    // Make sure current preview data in session exists and is up-to-date.\n    clearPreviewData()\n        .then(function () { return setPreviewData(); })\n        .then(function () { return reloadIframe(); });\n    // Remember last selected device size\n    var lastDevice = null;\n    try {\n        lastDevice = localStorage.getItem('wagtail:preview-panel-device');\n    }\n    catch (e) {\n        // Initialise with the default device if the last one cannot be restored.\n    }\n    var lastDeviceInput = previewPanel.querySelector(\"[data-device-width][value=\\\"\".concat(lastDevice, \"\\\"]\")) ||\n        defaultSizeInput;\n    lastDeviceInput.click();\n}\ndocument.addEventListener('DOMContentLoaded', function () {\n    initPreview();\n});\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL3ByZXZpZXctcGFuZWwuanMuanMiLCJtYXBwaW5ncyI6IkFBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSIsInNvdXJjZXMiOlsid2VicGFjazovL3dhZ3RhaWwvLi9jbGllbnQvc3JjL2VudHJ5cG9pbnRzL2FkbWluL3ByZXZpZXctcGFuZWwuanM/NTEwYyJdLCJzb3VyY2VzQ29udGVudCI6WyJcInVzZSBzdHJpY3RcIjtcbmV4cG9ydHMuX19lc01vZHVsZSA9IHRydWU7XG52YXIgd2FndGFpbENvbmZpZ18xID0gcmVxdWlyZShcIi4uLy4uL2NvbmZpZy93YWd0YWlsQ29uZmlnXCIpO1xudmFyIGdldHRleHRfMSA9IHJlcXVpcmUoXCIuLi8uLi91dGlscy9nZXR0ZXh0XCIpO1xuZnVuY3Rpb24gaW5pdFByZXZpZXcoKSB7XG4gICAgdmFyIHByZXZpZXdTaWRlUGFuZWwgPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKCdbZGF0YS1zaWRlLXBhbmVsPVwicHJldmlld1wiXScpO1xuICAgIC8vIFByZXZpZXcgc2lkZSBwYW5lbCBpcyBub3Qgc2hvd24gaWYgdGhlIG9iamVjdCBkb2VzIG5vdCBoYXZlIGFueSBwcmV2aWV3IG1vZGVzXG4gICAgaWYgKCFwcmV2aWV3U2lkZVBhbmVsKVxuICAgICAgICByZXR1cm47XG4gICAgLy8gVGhlIHByZXZpZXdTaWRlUGFuZWwgaXMgYSBnZW5lcmljIGNvbnRhaW5lciBmb3Igc2lkZSBwYW5lbHMsXG4gICAgLy8gdGhlIGNvbnRlbnQgb2YgdGhlIHByZXZpZXcgcGFuZWwgaXRzZWxmIGlzIGluIGEgY2hpbGQgZWxlbWVudFxuICAgIHZhciBwcmV2aWV3UGFuZWwgPSBwcmV2aWV3U2lkZVBhbmVsLnF1ZXJ5U2VsZWN0b3IoJ1tkYXRhLXByZXZpZXctcGFuZWxdJyk7XG4gICAgLy9cbiAgICAvLyBQcmV2aWV3IHNpemUgaGFuZGxpbmdcbiAgICAvL1xuICAgIHZhciBzaXplSW5wdXRzID0gcHJldmlld1BhbmVsLnF1ZXJ5U2VsZWN0b3JBbGwoJ1tkYXRhLWRldmljZS13aWR0aF0nKTtcbiAgICB2YXIgZGVmYXVsdFNpemVJbnB1dCA9IHByZXZpZXdQYW5lbC5xdWVyeVNlbGVjdG9yKCdbZGF0YS1kZWZhdWx0LXNpemVdJyk7XG4gICAgdmFyIHNldFByZXZpZXdXaWR0aCA9IGZ1bmN0aW9uICh3aWR0aCkge1xuICAgICAgICB2YXIgaXNVbmF2YWlsYWJsZSA9IHByZXZpZXdQYW5lbC5jbGFzc0xpc3QuY29udGFpbnMoJ3ByZXZpZXctcGFuZWwtLXVuYXZhaWxhYmxlJyk7XG4gICAgICAgIHZhciBkZXZpY2VXaWR0aCA9IHdpZHRoO1xuICAgICAgICAvLyBSZXNldCB0byBkZWZhdWx0IHNpemUgaWYgd2lkdGggaXMgZmFsc3kgb3IgcHJldmlldyBpcyB1bmF2YWlsYWJsZVxuICAgICAgICBpZiAoIXdpZHRoIHx8IGlzVW5hdmFpbGFibGUpIHtcbiAgICAgICAgICAgIGRldmljZVdpZHRoID0gZGVmYXVsdFNpemVJbnB1dC5kYXRhc2V0LmRldmljZVdpZHRoO1xuICAgICAgICB9XG4gICAgICAgIHByZXZpZXdQYW5lbC5zdHlsZS5zZXRQcm9wZXJ0eSgnLS1wcmV2aWV3LWRldmljZS13aWR0aCcsIGRldmljZVdpZHRoKTtcbiAgICB9O1xuICAgIHZhciB0b2dnbGVQcmV2aWV3U2l6ZSA9IGZ1bmN0aW9uIChldmVudCkge1xuICAgICAgICB2YXIgZGV2aWNlID0gZXZlbnQudGFyZ2V0LnZhbHVlO1xuICAgICAgICB2YXIgZGV2aWNlV2lkdGggPSBldmVudC50YXJnZXQuZGF0YXNldC5kZXZpY2VXaWR0aDtcbiAgICAgICAgc2V0UHJldmlld1dpZHRoKGRldmljZVdpZHRoKTtcbiAgICAgICAgdHJ5IHtcbiAgICAgICAgICAgIGxvY2FsU3RvcmFnZS5zZXRJdGVtKCd3YWd0YWlsOnByZXZpZXctcGFuZWwtZGV2aWNlJywgZGV2aWNlKTtcbiAgICAgICAgfVxuICAgICAgICBjYXRjaCAoZSkge1xuICAgICAgICAgICAgLy8gU2tpcCBzYXZpbmcgdGhlIGRldmljZSBpZiBsb2NhbFN0b3JhZ2UgZmFpbHMuXG4gICAgICAgIH1cbiAgICAgICAgLy8gRW5zdXJlIG9ubHkgb25lIGRldmljZSBjbGFzcyBpcyBhcHBsaWVkXG4gICAgICAgIHNpemVJbnB1dHMuZm9yRWFjaChmdW5jdGlvbiAoaW5wdXQpIHtcbiAgICAgICAgICAgIHByZXZpZXdQYW5lbC5jbGFzc0xpc3QudG9nZ2xlKFwicHJldmlldy1wYW5lbC0tXCIuY29uY2F0KGlucHV0LnZhbHVlKSwgaW5wdXQudmFsdWUgPT09IGRldmljZSk7XG4gICAgICAgIH0pO1xuICAgIH07XG4gICAgc2l6ZUlucHV0cy5mb3JFYWNoKGZ1bmN0aW9uIChpbnB1dCkge1xuICAgICAgICByZXR1cm4gaW5wdXQuYWRkRXZlbnRMaXN0ZW5lcignY2hhbmdlJywgdG9nZ2xlUHJldmlld1NpemUpO1xuICAgIH0pO1xuICAgIHZhciByZXNpemVPYnNlcnZlciA9IG5ldyBSZXNpemVPYnNlcnZlcihmdW5jdGlvbiAoZW50cmllcykge1xuICAgICAgICByZXR1cm4gcHJldmlld1BhbmVsLnN0eWxlLnNldFByb3BlcnR5KCctLXByZXZpZXctcGFuZWwtd2lkdGgnLCBlbnRyaWVzWzBdLmNvbnRlbnRSZWN0LndpZHRoKTtcbiAgICB9KTtcbiAgICByZXNpemVPYnNlcnZlci5vYnNlcnZlKHByZXZpZXdQYW5lbCk7XG4gICAgLy9cbiAgICAvLyBQcmV2aWV3IGRhdGEgaGFuZGxpbmdcbiAgICAvL1xuICAgIC8vIEluIG9yZGVyIHRvIG1ha2UgdGhlIHByZXZpZXcgdHJ1bHkgcmVsaWFibGUsIHRoZSBwcmV2aWV3IHBhZ2UgbmVlZHNcbiAgICAvLyB0byBiZSBwZXJmZWN0bHkgaW5kZXBlbmRlbnQgZnJvbSB0aGUgZWRpdCBwYWdlLFxuICAgIC8vIGZyb20gdGhlIGJyb3dzZXIgcGVyc3BlY3RpdmUuIFRvIHBhc3MgZGF0YSBmcm9tIHRoZSBlZGl0IHBhZ2VcbiAgICAvLyB0byB0aGUgcHJldmlldyBwYWdlLCB3ZSBzZW5kIHRoZSBmb3JtIGFmdGVyIGVhY2ggY2hhbmdlXG4gICAgLy8gYW5kIHNhdmUgaXQgaW5zaWRlIHRoZSB1c2VyIHNlc3Npb24uXG4gICAgdmFyIG5ld1RhYkJ1dHRvbiA9IHByZXZpZXdQYW5lbC5xdWVyeVNlbGVjdG9yKCdbZGF0YS1wcmV2aWV3LW5ldy10YWJdJyk7XG4gICAgdmFyIHJlZnJlc2hCdXR0b24gPSBwcmV2aWV3UGFuZWwucXVlcnlTZWxlY3RvcignW2RhdGEtcmVmcmVzaC1wcmV2aWV3XScpO1xuICAgIHZhciBsb2FkaW5nU3Bpbm5lciA9IHByZXZpZXdQYW5lbC5xdWVyeVNlbGVjdG9yKCdbZGF0YS1wcmV2aWV3LXNwaW5uZXJdJyk7XG4gICAgdmFyIGZvcm0gPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKCdbZGF0YS1lZGl0LWZvcm1dJyk7XG4gICAgdmFyIHByZXZpZXdVcmwgPSBwcmV2aWV3UGFuZWwuZGF0YXNldC5hY3Rpb247XG4gICAgdmFyIHByZXZpZXdNb2RlU2VsZWN0ID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcignW2RhdGEtcHJldmlldy1tb2RlLXNlbGVjdF0nKTtcbiAgICB2YXIgaWZyYW1lID0gcHJldmlld1BhbmVsLnF1ZXJ5U2VsZWN0b3IoJ1tkYXRhLXByZXZpZXctaWZyYW1lXScpO1xuICAgIHZhciBzcGlubmVyVGltZW91dDtcbiAgICB2YXIgaGFzUGVuZGluZ1VwZGF0ZSA9IGZhbHNlO1xuICAgIHZhciBmaW5pc2hVcGRhdGUgPSBmdW5jdGlvbiAoKSB7XG4gICAgICAgIGNsZWFyVGltZW91dChzcGlubmVyVGltZW91dCk7XG4gICAgICAgIGxvYWRpbmdTcGlubmVyLmNsYXNzTGlzdC5hZGQoJ3ctaGlkZGVuJyk7XG4gICAgICAgIGhhc1BlbmRpbmdVcGRhdGUgPSBmYWxzZTtcbiAgICB9O1xuICAgIHZhciByZWxvYWRJZnJhbWUgPSBmdW5jdGlvbiAoKSB7XG4gICAgICAgIC8vIEluc3RlYWQgb2YgcmVsb2FkaW5nIHRoZSBpZnJhbWUsIHdlJ3JlIHJlcGxhY2luZyBpdCB3aXRoIGEgbmV3IGlmcmFtZSB0b1xuICAgICAgICAvLyBwcmV2ZW50IGZsYXNoaW5nXG4gICAgICAgIC8vIENyZWF0ZSBhIG5ldyBpbnZpc2libGUgaWZyYW1lIGVsZW1lbnRcbiAgICAgICAgdmFyIG5ld0lmcmFtZSA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoJ2lmcmFtZScpO1xuICAgICAgICBuZXdJZnJhbWUuc3R5bGUud2lkdGggPSAwO1xuICAgICAgICBuZXdJZnJhbWUuc3R5bGUuaGVpZ2h0ID0gMDtcbiAgICAgICAgbmV3SWZyYW1lLnN0eWxlLm9wYWNpdHkgPSAwO1xuICAgICAgICBuZXdJZnJhbWUuc3R5bGUucG9zaXRpb24gPSAnYWJzb2x1dGUnO1xuICAgICAgICBuZXdJZnJhbWUuc3JjID0gaWZyYW1lLnNyYztcbiAgICAgICAgLy8gUHV0IGl0IGluIHRoZSBET00gc28gaXQgbG9hZHMgdGhlIHBhZ2VcbiAgICAgICAgaWZyYW1lLmluc2VydEFkamFjZW50RWxlbWVudCgnYWZ0ZXJlbmQnLCBuZXdJZnJhbWUpO1xuICAgICAgICB2YXIgaGFuZGxlTG9hZCA9IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIC8vIENvcHkgYWxsIGF0dHJpYnV0ZXMgZnJvbSB0aGUgb2xkIGlmcmFtZSB0byB0aGUgbmV3IG9uZSxcbiAgICAgICAgICAgIC8vIGV4Y2VwdCBzcmMgYXMgdGhhdCB3aWxsIGNhdXNlIHRoZSBpZnJhbWUgdG8gYmUgcmVsb2FkZWRcbiAgICAgICAgICAgIEFycmF5LmZyb20oaWZyYW1lLmF0dHJpYnV0ZXMpLmZvckVhY2goZnVuY3Rpb24gKGtleSkge1xuICAgICAgICAgICAgICAgIGlmIChrZXkubm9kZU5hbWUgPT09ICdzcmMnKVxuICAgICAgICAgICAgICAgICAgICByZXR1cm47XG4gICAgICAgICAgICAgICAgbmV3SWZyYW1lLnNldEF0dHJpYnV0ZShrZXkubm9kZU5hbWUsIGtleS5ub2RlVmFsdWUpO1xuICAgICAgICAgICAgfSk7XG4gICAgICAgICAgICAvLyBSZXN0b3JlIHNjcm9sbCBwb3NpdGlvblxuICAgICAgICAgICAgbmV3SWZyYW1lLmNvbnRlbnRXaW5kb3cuc2Nyb2xsKGlmcmFtZS5jb250ZW50V2luZG93LnNjcm9sbFgsIGlmcmFtZS5jb250ZW50V2luZG93LnNjcm9sbFkpO1xuICAgICAgICAgICAgLy8gUmVtb3ZlIHRoZSBvbGQgaWZyYW1lIGFuZCBzd2FwIGl0IHdpdGggdGhlIG5ldyBvbmVcbiAgICAgICAgICAgIGlmcmFtZS5yZW1vdmUoKTtcbiAgICAgICAgICAgIGlmcmFtZSA9IG5ld0lmcmFtZTtcbiAgICAgICAgICAgIC8vIE1ha2UgdGhlIG5ldyBpZnJhbWUgdmlzaWJsZVxuICAgICAgICAgICAgbmV3SWZyYW1lLnN0eWxlID0gbnVsbDtcbiAgICAgICAgICAgIC8vIFJlYWR5IGZvciBhbm90aGVyIHVwZGF0ZVxuICAgICAgICAgICAgZmluaXNoVXBkYXRlKCk7XG4gICAgICAgICAgICAvLyBSZW1vdmUgdGhlIGxvYWQgZXZlbnQgbGlzdGVuZXIgc28gaXQgZG9lc24ndCBmaXJlIHdoZW4gc3dpdGNoaW5nIG1vZGVzXG4gICAgICAgICAgICBuZXdJZnJhbWUucmVtb3ZlRXZlbnRMaXN0ZW5lcignbG9hZCcsIGhhbmRsZUxvYWQpO1xuICAgICAgICB9O1xuICAgICAgICBuZXdJZnJhbWUuYWRkRXZlbnRMaXN0ZW5lcignbG9hZCcsIGhhbmRsZUxvYWQpO1xuICAgIH07XG4gICAgdmFyIGNsZWFyUHJldmlld0RhdGEgPSBmdW5jdGlvbiAoKSB7XG4gICAgICAgIHZhciBfYTtcbiAgICAgICAgcmV0dXJuIGZldGNoKHByZXZpZXdVcmwsIHtcbiAgICAgICAgICAgIGhlYWRlcnM6IChfYSA9IHt9LCBfYVt3YWd0YWlsQ29uZmlnXzEuV0FHVEFJTF9DT05GSUcuQ1NSRl9IRUFERVJfTkFNRV0gPSB3YWd0YWlsQ29uZmlnXzEuV0FHVEFJTF9DT05GSUcuQ1NSRl9UT0tFTiwgX2EpLFxuICAgICAgICAgICAgbWV0aG9kOiAnREVMRVRFJ1xuICAgICAgICB9KTtcbiAgICB9O1xuICAgIHZhciBzZXRQcmV2aWV3RGF0YSA9IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgLy8gQmFpbCBvdXQgaWYgdGhlcmUgaXMgYWxyZWFkeSBhIHBlbmRpbmcgdXBkYXRlXG4gICAgICAgIGlmIChoYXNQZW5kaW5nVXBkYXRlKVxuICAgICAgICAgICAgcmV0dXJuIFByb21pc2UucmVzb2x2ZSgpO1xuICAgICAgICBoYXNQZW5kaW5nVXBkYXRlID0gdHJ1ZTtcbiAgICAgICAgc3Bpbm5lclRpbWVvdXQgPSBzZXRUaW1lb3V0KGZ1bmN0aW9uICgpIHsgcmV0dXJuIGxvYWRpbmdTcGlubmVyLmNsYXNzTGlzdC5yZW1vdmUoJ3ctaGlkZGVuJyk7IH0sIDIwMDApO1xuICAgICAgICByZXR1cm4gZmV0Y2gocHJldmlld1VybCwge1xuICAgICAgICAgICAgbWV0aG9kOiAnUE9TVCcsXG4gICAgICAgICAgICBib2R5OiBuZXcgRm9ybURhdGEoZm9ybSlcbiAgICAgICAgfSlcbiAgICAgICAgICAgIC50aGVuKGZ1bmN0aW9uIChyZXNwb25zZSkgeyByZXR1cm4gcmVzcG9uc2UuanNvbigpOyB9KVxuICAgICAgICAgICAgLnRoZW4oZnVuY3Rpb24gKGRhdGEpIHtcbiAgICAgICAgICAgIHByZXZpZXdQYW5lbC5jbGFzc0xpc3QudG9nZ2xlKCdwcmV2aWV3LXBhbmVsLS1oYXMtZXJyb3JzJywgIWRhdGEuaXNfdmFsaWQpO1xuICAgICAgICAgICAgcHJldmlld1BhbmVsLmNsYXNzTGlzdC50b2dnbGUoJ3ByZXZpZXctcGFuZWwtLXVuYXZhaWxhYmxlJywgIWRhdGEuaXNfYXZhaWxhYmxlKTtcbiAgICAgICAgICAgIGlmIChkYXRhLmlzX3ZhbGlkKSB7XG4gICAgICAgICAgICAgICAgcmVsb2FkSWZyYW1lKCk7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgICAgICBmaW5pc2hVcGRhdGUoKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIHJldHVybiBkYXRhLmlzX3ZhbGlkO1xuICAgICAgICB9KVtcImNhdGNoXCJdKGZ1bmN0aW9uIChlcnJvcikge1xuICAgICAgICAgICAgZmluaXNoVXBkYXRlKCk7XG4gICAgICAgICAgICAvLyBSZS10aHJvdyBlcnJvciBzbyBpdCBjYW4gYmUgaGFuZGxlZCBieSBoYW5kbGVQcmV2aWV3XG4gICAgICAgICAgICB0aHJvdyBlcnJvcjtcbiAgICAgICAgfSk7XG4gICAgfTtcbiAgICB2YXIgaGFuZGxlUHJldmlldyA9IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgcmV0dXJuIHNldFByZXZpZXdEYXRhKClbXCJjYXRjaFwiXShmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICAvLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgbm8tYWxlcnRcbiAgICAgICAgICAgIHdpbmRvdy5hbGVydCgoMCwgZ2V0dGV4dF8xLmdldHRleHQpKCdFcnJvciB3aGlsZSBzZW5kaW5nIHByZXZpZXcgZGF0YS4nKSk7XG4gICAgICAgIH0pO1xuICAgIH07XG4gICAgdmFyIGhhbmRsZVByZXZpZXdJbk5ld1RhYiA9IGZ1bmN0aW9uIChldmVudCkge1xuICAgICAgICBldmVudC5wcmV2ZW50RGVmYXVsdCgpO1xuICAgICAgICB2YXIgcHJldmlld1dpbmRvdyA9IHdpbmRvdy5vcGVuKCcnLCBwcmV2aWV3VXJsKTtcbiAgICAgICAgcHJldmlld1dpbmRvdy5mb2N1cygpO1xuICAgICAgICBoYW5kbGVQcmV2aWV3KCkudGhlbihmdW5jdGlvbiAoc3VjY2Vzcykge1xuICAgICAgICAgICAgaWYgKHN1Y2Nlc3MpIHtcbiAgICAgICAgICAgICAgICB2YXIgdXJsID0gbmV3IFVSTChuZXdUYWJCdXR0b24uaHJlZik7XG4gICAgICAgICAgICAgICAgcHJldmlld1dpbmRvdy5kb2N1bWVudC5sb2NhdGlvbiA9IHVybC50b1N0cmluZygpO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgZWxzZSB7XG4gICAgICAgICAgICAgICAgd2luZG93LmZvY3VzKCk7XG4gICAgICAgICAgICAgICAgcHJldmlld1dpbmRvdy5jbG9zZSgpO1xuICAgICAgICAgICAgfVxuICAgICAgICB9KTtcbiAgICB9O1xuICAgIG5ld1RhYkJ1dHRvbi5hZGRFdmVudExpc3RlbmVyKCdjbGljaycsIGhhbmRsZVByZXZpZXdJbk5ld1RhYik7XG4gICAgaWYgKHJlZnJlc2hCdXR0b24pIHtcbiAgICAgICAgcmVmcmVzaEJ1dHRvbi5hZGRFdmVudExpc3RlbmVyKCdjbGljaycsIGhhbmRsZVByZXZpZXcpO1xuICAgIH1cbiAgICBpZiAod2FndGFpbENvbmZpZ18xLldBR1RBSUxfQ09ORklHLldBR1RBSUxfQVVUT19VUERBVEVfUFJFVklFVykge1xuICAgICAgICB2YXIgb2xkUGF5bG9hZF8xID0gbmV3IFVSTFNlYXJjaFBhcmFtcyhuZXcgRm9ybURhdGEoZm9ybSkpLnRvU3RyaW5nKCk7XG4gICAgICAgIHZhciB1cGRhdGVJbnRlcnZhbF8xO1xuICAgICAgICB2YXIgaGFzQ2hhbmdlc18xID0gZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgdmFyIG5ld1BheWxvYWQgPSBuZXcgVVJMU2VhcmNoUGFyYW1zKG5ldyBGb3JtRGF0YShmb3JtKSkudG9TdHJpbmcoKTtcbiAgICAgICAgICAgIHZhciBjaGFuZ2VkID0gb2xkUGF5bG9hZF8xICE9PSBuZXdQYXlsb2FkO1xuICAgICAgICAgICAgb2xkUGF5bG9hZF8xID0gbmV3UGF5bG9hZDtcbiAgICAgICAgICAgIHJldHVybiBjaGFuZ2VkO1xuICAgICAgICB9O1xuICAgICAgICB2YXIgY2hlY2tBbmRVcGRhdGVQcmV2aWV3XzEgPSBmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICAvLyBEbyBub3QgY2hlY2sgZm9yIHByZXZpZXcgdXBkYXRlIGlmIGFuIHVwZGF0ZSByZXF1ZXN0IGlzIHN0aWxsIHBlbmRpbmdcbiAgICAgICAgICAgIC8vIGFuZCBkb24ndCBzZW5kIGEgbmV3IHJlcXVlc3QgaWYgdGhlIGZvcm0gaGFzbid0IGNoYW5nZWRcbiAgICAgICAgICAgIGlmIChoYXNQZW5kaW5nVXBkYXRlIHx8ICFoYXNDaGFuZ2VzXzEoKSlcbiAgICAgICAgICAgICAgICByZXR1cm47XG4gICAgICAgICAgICBzZXRQcmV2aWV3RGF0YSgpO1xuICAgICAgICB9O1xuICAgICAgICBwcmV2aWV3U2lkZVBhbmVsLmFkZEV2ZW50TGlzdGVuZXIoJ3Nob3cnLCBmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICAvLyBJbW1lZGlhdGVseSB1cGRhdGUgdGhlIHByZXZpZXcgd2hlbiB0aGUgcGFuZWwgaXMgb3BlbmVkXG4gICAgICAgICAgICBjaGVja0FuZFVwZGF0ZVByZXZpZXdfMSgpO1xuICAgICAgICAgICAgLy8gT25seSBzZXQgdGhlIGludGVydmFsIHdoaWxlIHRoZSBwYW5lbCBpcyBzaG93blxuICAgICAgICAgICAgdXBkYXRlSW50ZXJ2YWxfMSA9IHNldEludGVydmFsKGNoZWNrQW5kVXBkYXRlUHJldmlld18xLCB3YWd0YWlsQ29uZmlnXzEuV0FHVEFJTF9DT05GSUcuV0FHVEFJTF9BVVRPX1VQREFURV9QUkVWSUVXX0lOVEVSVkFMKTtcbiAgICAgICAgfSk7XG4gICAgICAgIHByZXZpZXdTaWRlUGFuZWwuYWRkRXZlbnRMaXN0ZW5lcignaGlkZScsIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIGNsZWFySW50ZXJ2YWwodXBkYXRlSW50ZXJ2YWxfMSk7XG4gICAgICAgIH0pO1xuICAgIH1cbiAgICAvL1xuICAgIC8vIFByZXZpZXcgbW9kZSBoYW5kbGluZ1xuICAgIC8vXG4gICAgdmFyIGhhbmRsZVByZXZpZXdNb2RlQ2hhbmdlID0gZnVuY3Rpb24gKGV2ZW50KSB7XG4gICAgICAgIHZhciBtb2RlID0gZXZlbnQudGFyZ2V0LnZhbHVlO1xuICAgICAgICB2YXIgdXJsID0gbmV3IFVSTChpZnJhbWUuc3JjKTtcbiAgICAgICAgdXJsLnNlYXJjaFBhcmFtcy5zZXQoJ21vZGUnLCBtb2RlKTtcbiAgICAgICAgaWZyYW1lLnNyYyA9IHVybC50b1N0cmluZygpO1xuICAgICAgICB1cmwuc2VhcmNoUGFyYW1zW1wiZGVsZXRlXCJdKCdpbl9wcmV2aWV3X3BhbmVsJyk7XG4gICAgICAgIG5ld1RhYkJ1dHRvbi5ocmVmID0gdXJsLnRvU3RyaW5nKCk7XG4gICAgICAgIC8vIE1ha2Ugc3VyZSBkYXRhIGlzIHVwZGF0ZWRcbiAgICAgICAgaGFuZGxlUHJldmlldygpO1xuICAgIH07XG4gICAgaWYgKHByZXZpZXdNb2RlU2VsZWN0KSB7XG4gICAgICAgIHByZXZpZXdNb2RlU2VsZWN0LmFkZEV2ZW50TGlzdGVuZXIoJ2NoYW5nZScsIGhhbmRsZVByZXZpZXdNb2RlQ2hhbmdlKTtcbiAgICB9XG4gICAgLy8gTWFrZSBzdXJlIGN1cnJlbnQgcHJldmlldyBkYXRhIGluIHNlc3Npb24gZXhpc3RzIGFuZCBpcyB1cC10by1kYXRlLlxuICAgIGNsZWFyUHJldmlld0RhdGEoKVxuICAgICAgICAudGhlbihmdW5jdGlvbiAoKSB7IHJldHVybiBzZXRQcmV2aWV3RGF0YSgpOyB9KVxuICAgICAgICAudGhlbihmdW5jdGlvbiAoKSB7IHJldHVybiByZWxvYWRJZnJhbWUoKTsgfSk7XG4gICAgLy8gUmVtZW1iZXIgbGFzdCBzZWxlY3RlZCBkZXZpY2Ugc2l6ZVxuICAgIHZhciBsYXN0RGV2aWNlID0gbnVsbDtcbiAgICB0cnkge1xuICAgICAgICBsYXN0RGV2aWNlID0gbG9jYWxTdG9yYWdlLmdldEl0ZW0oJ3dhZ3RhaWw6cHJldmlldy1wYW5lbC1kZXZpY2UnKTtcbiAgICB9XG4gICAgY2F0Y2ggKGUpIHtcbiAgICAgICAgLy8gSW5pdGlhbGlzZSB3aXRoIHRoZSBkZWZhdWx0IGRldmljZSBpZiB0aGUgbGFzdCBvbmUgY2Fubm90IGJlIHJlc3RvcmVkLlxuICAgIH1cbiAgICB2YXIgbGFzdERldmljZUlucHV0ID0gcHJldmlld1BhbmVsLnF1ZXJ5U2VsZWN0b3IoXCJbZGF0YS1kZXZpY2Utd2lkdGhdW3ZhbHVlPVxcXCJcIi5jb25jYXQobGFzdERldmljZSwgXCJcXFwiXVwiKSkgfHxcbiAgICAgICAgZGVmYXVsdFNpemVJbnB1dDtcbiAgICBsYXN0RGV2aWNlSW5wdXQuY2xpY2soKTtcbn1cbmRvY3VtZW50LmFkZEV2ZW50TGlzdGVuZXIoJ0RPTUNvbnRlbnRMb2FkZWQnLCBmdW5jdGlvbiAoKSB7XG4gICAgaW5pdFByZXZpZXcoKTtcbn0pO1xuIl0sIm5hbWVzIjpbXSwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///./client/src/entrypoints/admin/preview-panel.js\n");

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
/******/ 			"preview-panel": 0
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
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["wagtail/admin/static/wagtailadmin/js/vendor"], () => (__webpack_require__("./client/src/entrypoints/admin/preview-panel.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;