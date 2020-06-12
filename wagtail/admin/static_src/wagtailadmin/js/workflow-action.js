/* When a workflow action button is clicked, either show a modal or make a POST request to the workflow action view */
function ActivateWorkflowActions(csrfToken) {
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

                var csrftokenElement = document.createElement('input');
                csrftokenElement.type = 'hidden';
                csrftokenElement.name = 'csrfmiddlewaretoken';
                csrftokenElement.value = csrfToken;
                formElement.appendChild(csrftokenElement);

                var nextElement = document.createElement('input');
                nextElement.type = 'hidden';
                nextElement.name = 'next';
                nextElement.value = window.location;
                formElement.appendChild(nextElement);

                document.body.appendChild(formElement);
                formElement.submit();
            }
        }, {capture: true});
    });
}