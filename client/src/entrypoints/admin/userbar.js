import { Userbar } from '../../includes/userbar';

customElements.define('wagtail-userbar', Userbar);

window.wagtail = window.wagtail || {};
window.wagtail.userbar = document.querySelector('wagtail-userbar');
