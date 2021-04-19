/* When a lock/unlock action button is clicked, make a POST request to the relevant view */

function LockUnlockAction(csrfToken, next) {
  const actionElements = document.querySelectorAll('[data-locking-action]');
  [...actionElements].forEach((buttonElement) => {
    buttonElement.addEventListener('click', (e) => {
      // Stop the button from submitting the form
      e.preventDefault();
      e.stopPropagation();

      const formElement = document.createElement('form');

      formElement.action = buttonElement.dataset.lockingAction;
      formElement.method = 'POST';

      const csrftokenElement = document.createElement('input');
      csrftokenElement.type = 'hidden';
      csrftokenElement.name = 'csrfmiddlewaretoken';
      csrftokenElement.value = csrfToken;
      formElement.appendChild(csrftokenElement);

      if (typeof next !== 'undefined') {
        const nextElement = document.createElement('input');
        nextElement.type = 'hidden';
        nextElement.name = 'next';
        nextElement.value = next;
        formElement.appendChild(nextElement);
      }

      document.body.appendChild(formElement);
      formElement.submit();
    }, { capture: true });
  });
}
window.LockUnlockAction = LockUnlockAction;
