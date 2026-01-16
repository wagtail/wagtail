import { Userbar } from '../../includes/userbar';

customElements.define('wagtail-userbar', Userbar);

window.wagtailUserbar = document.querySelector('wagtail-userbar');
