/* When a lock/unlock action button is clicked, make a POST request to the relevant view */

function LockUnlockAction(csrfToken, next) {
  document.querySelectorAll('[data-locking-action]').forEach(function (buttonElement) {
    buttonElement.addEventListener('click', function (e) {
      // Stop the button from submitting the form
      e.preventDefault();
      e.stopPropagation();

      var formElement = document.createElement('form');

      formElement.action = buttonElement.dataset.lockingAction;
      formElement.method = 'POST';

      var csrftokenElement = document.createElement('input');
      csrftokenElement.type = 'hidden';
      csrftokenElement.name = 'csrfmiddlewaretoken';
      csrftokenElement.value = csrfToken;
      formElement.appendChild(csrftokenElement);

      if (typeof next !== 'undefined') {
        var nextElement = document.createElement('input');
        nextElement.type = 'hidden';
        nextElement.name = 'next';
        nextElement.value = next;
        formElement.appendChild(nextElement);
      }

      document.body.appendChild(formElement);
      formElement.submit();
    }, {capture: true});
  });
}
