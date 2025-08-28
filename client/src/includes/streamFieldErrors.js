import { escapeHtml as h } from '../utils/text';

const updateEvent = new Event('w-streamfield:update');

const removeErrorMessages = (container) => {
  container
    .querySelectorAll(':scope > .help-block.help-critical')
    .forEach((element) => element.remove());
  window.dispatchEvent(updateEvent);
};

const addErrorMessages = (container, messages) => {
  messages.forEach((message) => {
    const errorElement = document.createElement('p');
    errorElement.classList.add('help-block');
    errorElement.classList.add('help-critical');
    errorElement.innerHTML = h(message);
    container.insertBefore(errorElement, container.childNodes[0]);
  });
  window.dispatchEvent(updateEvent);
};

export { removeErrorMessages, addErrorMessages };
