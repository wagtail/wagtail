import React, { useMemo } from 'react';
import Tippy from '@tippyjs/react';

// Conditionally render tippy tooltips surrounding elements
const TippyWrapper = ({ condition, children, label, placement }) =>
  useMemo(
    () =>
      condition ? (
        <Tippy content={label} placement={placement}>
          {children}
        </Tippy>
      ) : (
        children
      ),
    [children],
  );

export default TippyWrapper;
