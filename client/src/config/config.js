export const PAGES_ROOT_ID = 'root';

export const EXPLORER_ANIM_DURATION = 220;

// TODO Add back in when we want to support explorer that displays pages
// without children (API call without has_children=1).
export const EXPLORER_FILTERS = [
  { id: 1, label: 'A', filter: null },
  { id: 2, label: 'B', filter: 'has_children=1' }
];
