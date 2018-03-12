/* A framework for modal popups that are loaded via AJAX, allowing navigation to other
subpages to happen within the lightbox, and returning a response to the calling page,
possibly after several navigation steps
*/

function ModalWorkflow(opts) {
    /* options passed in 'opts':
        'url' (required): initial
        'responses' (optional): dict of callbacks to be called when the modal content
            calls modal.respond(callbackName, params)
    */

    var self = {};
    var responseCallbacks = opts.responses || {};
    var errorCallback = opts.onError || function () {};

    /* remove any previous modals before continuing (closing doesn't remove them from the dom) */
    $('body > .modal').remove();

    // set default contents of container
    var container = $('<div class="modal fade" tabindex="-1" role="dialog" aria-hidden="true">\n    <div class="modal-dialog">\n        <div class="modal-content">\n            <button type="button" class="button close icon text-replace icon-cross" data-dismiss="modal" aria-hidden="true">&times;</button>\n            <div class="modal-body"></div>\n        </div><!-- /.modal-content -->\n    </div><!-- /.modal-dialog -->\n</div>');

    // add container to body and hide it, so content can be added to it before display
    $('body').append(container);
    container.modal('hide');

    self.body = container.find('.modal-body');

    self.loadUrl = function(url, urlParams) {
        $.get(url, urlParams, self.loadResponseText, 'text').fail(errorCallback);
    };

    self.postForm = function(url, formData) {
        $.post(url, formData, self.loadResponseText, 'text').fail(errorCallback);
    };

    self.ajaxifyForm = function(formSelector) {
        $(formSelector).each(function() {
            var action = this.action;
            if (this.method.toLowerCase() == 'get') {
                $(this).on('submit', function() {
                    self.loadUrl(action, $(this).serialize());
                    return false;
                });
            } else {
                $(this).on('submit', function() {
                    self.postForm(action, $(this).serialize());
                    return false;
                });
            }
        });
    };

    self.loadResponseText = function(responseText) {
        responseText = formJSON(responseText);

        var response;
        try {
            response = JSON.parse(responseText);
        } catch (e) {
            console.error("Could not parse JSON in loadResponseText:", responseText);
        }

        if (response) {
            self.loadBody(response);
        }
    };

    self.loadBody = function(response) {
        var html = response.html;
        if (html) {
            self.body.html(html);
            container.modal('show');
        }

        var onload = response.onload;
        if (onload) {
            var loader = document.createElement('script');
            var runner = '(' + onload + '(window.wagtail_modal_handler)); delete window.wagtail_modal_handler;';
            loader.textContent = runner;

            var head = document.getElementsByTagName('head')[0];
            window.wagtail_modal_handler = self;
            head.appendChild(loader);
        }
    };

    self.respond = function(responseType) {
        if (responseType in responseCallbacks) {
            args = Array.prototype.slice.call(arguments, 1);
            responseCallbacks[responseType].apply(self, args);
        }
    };

    self.close = function() {
        container.modal('hide');
    };

    self.loadUrl(opts.url, opts.urlParams);

    return self;
}


/* "static" helper function to turn Wagtail text responses into valid JSON. */
function formJSON(data) {
    var htmlKey = "'html':";
    var jsonHtmlKey = '"html":';

    if (data.indexOf(htmlKey) > -1) {
        data = data.replace(htmlKey, jsonHtmlKey);
        // The value for this key is already properly
        // JSON formatted by modal_workflow.py.
    }

    var onloadKey = "'onload':";
    var jsonOnloadKey = '"onload":';

    if (data.indexOf(onloadKey) > -1) {
        var parts = data.split(onloadKey);
        var sourceCode = parts[1].replace(/\s*\r?\n/g, '\\n').replace(/"/g, '\\"') + 'END_OF_RESPONSE';
        sourceCode = '"' + sourceCode.replace(/}[\s\r\n]*END_OF_RESPONSE/, '"}');
        data = parts[0] + jsonOnloadKey + sourceCode;
    }

    return data;
}

