/* When a lock/unlock action button is clicked, make a POST request to the relevant view */

function LockUnlockAction(csrfToken, next) {
  const actionElements = document.querySelectorAll('[data-action-lock-unlock]');
  actionElements.forEach((buttonElement) => {
    buttonElement.addEventListener(
      'click',
      (e) => {
        e.stopPropagation();

        const formElement = document.createElement('form');

        formElement.action = buttonElement.dataset.url;
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
      },
      { capture: true },
    );
  });
}
window.LockUnlockAction = LockUnlockAction;
