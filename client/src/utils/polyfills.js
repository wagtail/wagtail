/**
 * Polyfills for Wagtail's admin.
 */

// IE11.
import 'core-js/shim';
// IE11, old iOS Safari.
import 'whatwg-fetch';
// IE11.
import 'element-closest';
// IE11.
import { IS_IE11 } from '../config/wagtailConfig';
import svg4everybody from 'svg4everybody';

if (IS_IE11) {
  svg4everybody();
}
