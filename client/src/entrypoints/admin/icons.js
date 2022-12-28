import { initIconSprite } from '../../includes/initIconSprite';

const url = document.currentScript.dataset.iconUrl;
// <div data-sprite></div>
const container = document.querySelector('[data-sprite]');
initIconSprite(container, url);
