/**
 * Creates a debounced function that delays invoking func until after wait
 * milliseconds have elapsed since the last time the debounced function was invoked.
 * The debounced function comes with a cancel method to cancel delayed func invocations.
 */
export const debounce = (
  func: { (...args: any[]): void },
  wait = 0,
): { (...args: any[]): void; cancel(): void } => {
  let timeoutId: number | undefined;

  const debounced = (...args: any[]) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => {
      func(...args);
    }, wait);
  };

  debounced.cancel = () => {
    if (typeof timeoutId !== 'number') return;
    window.clearTimeout(timeoutId);
  };

  return debounced;
};
