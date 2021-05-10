export function clearfix() {
  return `
        &:before,
        &:after {
            content: ' ';
            display: table;
        }

        &:after {
            clear: both;
        }
    `;
}

export function visuallyhidden() {
  return `
        border: 0;
        clip: rect(0 0 0 0);
        height: 1px;
        margin: -1px;
        overflow: hidden;
        padding: 0;
        position: absolute;
        width: 1px;
    `;
}

export function transition(spec: string) {
  return `
        body.ready & {
            transition: ${spec};
        }
    `;
}

// Where included, show the focus outline within focusable items instead of around them.
// This is useful when focusable items are tightly packed and there is no space in-between.
export function showFocusOutlineInside() {
  return 'outline-offset: -1 * 3px;';  // 3px = $focus-outline-width
}
