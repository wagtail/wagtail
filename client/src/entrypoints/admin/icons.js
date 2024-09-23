import { initIconSprite } from '../../includes/initIconSprite';

const url = document.currentScript.dataset.iconUrl;
const container = document.querySelector('[data-sprite]');

initIconSprite(container, url);
