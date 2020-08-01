function _addHiddenInput(form, name, val) {
    var element = document.createElement('input');
    element.type = 'hidden';
    element.name = name;
    element.value = val;
    form.appendChild(element);
}

/* When a workflow action button is clicked, either show a modal or make a POST request to the workflow action view */
function ActivateWorkflowActionsForDashboard(csrfToken) {
    document.querySelectorAll('[data-workflow-action-url]').forEach(function (buttonElement) {
        buttonElement.addEventListener('click', function (e) {
            // Stop the button from submitting the form
            e.preventDefault();
            e.stopPropagation();

            if ('launchModal' in buttonElement.dataset) {
                ModalWorkflow({
                    'url': buttonElement.dataset.workflowActionUrl,
                    'onload': {
                        'action': function(modal, jsonData) {
                            var nextElement = document.createElement('input');
                            nextElement.type = 'hidden';
                            nextElement.name = 'next';
                            nextElement.value = window.location;
                            $('form', modal.body).append(nextElement);
                            modal.ajaxifyForm($('form', modal.body));
                        },
                        'success': function(modal, jsonData) {
                            window.location.href = jsonData['redirect'];
                        }
                    },
                });
            } else {
                // if not opening a modal, submit a POST request to the action url
                var formElement = document.createElement('form');

                formElement.action = buttonElement.dataset.workflowActionUrl;
                formElement.method = 'POST';

                _addHiddenInput(formElement, 'csrfmiddlewaretoken', csrfToken);
                _addHiddenInput(formElement, 'next', window.location);

                document.body.appendChild(formElement);
                formElement.submit();
            }
        }, {capture: true});
    });
}


function ActivateWorkflowActionsForEditView(formSelector) {
    var form = $(formSelector).get(0);

    document.querySelectorAll('[data-workflow-action-name]').forEach(function (buttonElement) {
        buttonElement.addEventListener('click', function (e) {
            if ('workflowActionModalUrl' in buttonElement.dataset) {
                // This action requires opening a modal to collect additional data.
                // Stop the button from submitting the form
                e.preventDefault();
                e.stopPropagation();

                // open the modal at the given URL
                ModalWorkflow({
                    'url': buttonElement.dataset.workflowActionModalUrl,
                    'onload': {
                        'action': function(modal, jsonData) {
                            modal.ajaxifyForm($('form', modal.body));
                        },
                        'success': function(modal, jsonData) {
                            // a success response includes the additional data to submit with the edit form
                            _addHiddenInput(form, 'action-workflow-action', 'true')
                            _addHiddenInput(form, 'workflow-action-name', buttonElement.dataset.workflowActionName)
                            _addHiddenInput(form, 'workflow-action-extra-data', JSON.stringify(jsonData['cleaned_data']))
                            // note: need to submit via jQuery (as opposed to form.submit()) so that the onsubmit handler
                            // that disables the dirty-form prompt doesn't get bypassed
                            $(form).submit();
                        }
                    },
                });

            } else {
                // no modal, so let the form submission to the edit view proceed, with additional
                // hidden inputs to tell it to perform our action
                _addHiddenInput(form, 'action-workflow-action', 'true')
                _addHiddenInput(form, 'workflow-action-name', buttonElement.dataset.workflowActionName)
            }
        }, {capture: true});
    });
}
