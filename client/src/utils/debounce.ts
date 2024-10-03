/**
 * Creates a debounced function that delays invoking func until after wait
 * milliseconds have elapsed since the last time the debounced function was invoked.
 * The debounced function comes with a cancel method to cancel delayed func invocations.
 *
 * If wait is provided as a non-number value the function will be invoked
 * immediately.
 *
 * When the debounced function is called it returns a promise that resolves with
 * the result of the invoked `func` or a rejected promise if calling the
 * function throws an error.
 *
 * @example
 * const debounced = debounce(() => console.log('Hello World!'), 1000);
 * debounced(); // logs 'Hello World!' after 1 second
 *
 * @example
 * const debounced = debounce(() => console.log('Hello World!'), null);
 * debounced(); // logs 'Hello World!' immediately
 *
 * @example
 * const debounced = debounce(() => window.screen, 500);
 * debounced().then((screen) => console.log(screen)); // returns current screen value after 500ms
 *
 * @example
 * const debounced = debounce(() => window.nothingHere.alsoNothing, 500);
 * debounced().catch((error) => console.log(error)); // logs error (TypeError: window.nothingHere is undefined) after 500ms
 *
 */
export const debounce = <A extends any[], R = any>(
  func: (...args: A) => R | Promise<R>,
  wait: number | null = 0,
): { (...args: A): Promise<R>; cancel(): void } => {
  let timeoutId: number | undefined;

  const debounced = (...args: A) => {
    window.clearTimeout(timeoutId);
    if (typeof wait !== 'number' || Number.isNaN(wait)) {
      try {
        return Promise.resolve<R>(func(...(args as A)));
      } catch (error) {
        return Promise.reject(error);
      }
    } else {
      return new Promise<R>((resolve, reject) => {
        timeoutId = window.setTimeout(() => {
          try {
            resolve(func(...(args as A)));
          } catch (error) {
            reject(error);
          }
        }, wait);
      });
    }
  };

  debounced.cancel = () => {
    if (typeof timeoutId !== 'number') return;
    window.clearTimeout(timeoutId);
  };

  return debounced;
};
