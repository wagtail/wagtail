import React, { useMemo } from 'react';
import Tippy from '@tippyjs/react';

interface TooltipWrapperProps {
  condition: boolean;
  children: React.ReactElement;
  label: string;
  placement: 'left' | 'right' | 'top' | 'bottom';
}

/**
 * Conditionally render Tippy tooltips surrounding elements
 */
const TooltipWrapper = ({
  condition,
  children,
  label,
  placement,
}: TooltipWrapperProps): React.ReactElement =>
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

export default TooltipWrapper;
