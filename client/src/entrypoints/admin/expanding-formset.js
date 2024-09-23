import { ExpandingFormset } from '../../components/ExpandingFormset';

function buildExpandingFormset(prefix, opts = {}) {
  return new ExpandingFormset(prefix, opts);
}
window.buildExpandingFormset = buildExpandingFormset;
