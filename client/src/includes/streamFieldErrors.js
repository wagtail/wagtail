import { escapeHtml as h } from '../utils/text';

const removeErrorMessages = (container) => {
  container
    .querySelectorAll(':scope > .help-block.help-critical')
    .forEach((element) => element.remove());
};

const addErrorMessages = (container, messages) => {
  messages.forEach((message) => {
    const errorElement = document.createElement('p');
    errorElement.classList.add('help-block');
    errorElement.classList.add('help-critical');
    errorElement.innerHTML = h(message);
    container.insertBefore(errorElement, container.childNodes[0]);
  });
};

export { removeErrorMessages, addErrorMessages };
