import { InlineUserbar } from '../../includes/inlineUserbar';
import { Userbar } from '../../includes/userbar';

customElements.define('wagtail-userbar', Userbar);
customElements.define('wagtail-inline-userbar', InlineUserbar);

window.wagtail = window.wagtail || {};
window.wagtail.userbar = document.querySelector('wagtail-userbar');
