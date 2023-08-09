import $ from 'jquery';

function addHiddenInput(form, name, val) {
  const element = document.createElement('input');
  element.type = 'hidden';
  element.name = name;
  element.value = val;
  form.appendChild(element);
}
// eslint-disable-next-line no-underscore-dangle
window._addHiddenInput = addHiddenInput;

/* When a workflow action button is clicked, either show a modal or make a POST request to the workflow action view */
function ActivateWorkflowActionsForDashboard(csrfToken) {
  const workflowActionElements = document.querySelectorAll(
    '[data-workflow-action-url]',
  );

  workflowActionElements.forEach((buttonElement) => {
    buttonElement.addEventListener(
      'click',
      (e) => {
        // Stop the button from submitting the form
        e.preventDefault();
        e.stopPropagation();

        if ('launchModal' in buttonElement.dataset) {
          // eslint-disable-next-line no-undef
          ModalWorkflow({
            url: buttonElement.dataset.workflowActionUrl,
            onload: {
              action(modal) {
                const nextElement = document.createElement('input');
                nextElement.type = 'hidden';
                nextElement.name = 'next';
                nextElement.value = window.location;
                $('form', modal.body).append(nextElement);
                modal.ajaxifyForm($('form', modal.body));
              },
              success(modal, jsonData) {
                window.location.href = jsonData.redirect;
              },
            },
          });
        } else {
          // if not opening a modal, submit a POST request to the action url
          const formElement = document.createElement('form');

          formElement.action = buttonElement.dataset.workflowActionUrl;
          formElement.method = 'POST';

          addHiddenInput(formElement, 'csrfmiddlewaretoken', csrfToken);
          addHiddenInput(formElement, 'next', window.location);

          document.body.appendChild(formElement);
          formElement.submit();
        }
      },
      { capture: true },
    );
  });
}
window.ActivateWorkflowActionsForDashboard =
  ActivateWorkflowActionsForDashboard;

function ActivateWorkflowActionsForEditView(formSelector) {
  const form = $(formSelector).get(0);

  const workflowActionElements = document.querySelectorAll(
    '[data-workflow-action-name]',
  );

  workflowActionElements.forEach((buttonElement) => {
    buttonElement.addEventListener(
      'click',
      (e) => {
        if ('workflowActionModalUrl' in buttonElement.dataset) {
          // This action requires opening a modal to collect additional data.
          // Stop the button from submitting the form
          e.preventDefault();
          e.stopPropagation();

          // open the modal at the given URL
          // eslint-disable-next-line no-undef
          ModalWorkflow({
            url: buttonElement.dataset.workflowActionModalUrl,
            onload: {
              action(modal) {
                modal.ajaxifyForm($('form', modal.body));
              },
              success(modal, jsonData) {
                // a success response includes the additional data to submit with the edit form
                addHiddenInput(form, 'action-workflow-action', 'true');
                addHiddenInput(
                  form,
                  'workflow-action-name',
                  buttonElement.dataset.workflowActionName,
                );
                addHiddenInput(
                  form,
                  'workflow-action-extra-data',
                  JSON.stringify(jsonData.cleaned_data),
                );
                // note: need to submit via jQuery (as opposed to form.submit()) so that the onsubmit handler
                // that disables the dirty-form prompt doesn't get bypassed
                $(form).submit();
              },
            },
          });
        } else {
          // no modal, so let the form submission to the edit view proceed, with additional
          // hidden inputs to tell it to perform our action
          addHiddenInput(form, 'action-workflow-action', 'true');
          addHiddenInput(
            form,
            'workflow-action-name',
            buttonElement.dataset.workflowActionName,
          );
        }
      },
      { capture: true },
    );
  });
}
window.ActivateWorkflowActionsForEditView = ActivateWorkflowActionsForEditView;
