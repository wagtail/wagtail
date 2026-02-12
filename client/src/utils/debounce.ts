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
export const debounce = <F extends AnyFunction>(
  func: F,
  wait: number | null = 0,
): DebouncedFunction<F> => {
  let timeoutId: number | undefined;

  const debounced = (...args: Parameters<F>) => {
    window.clearTimeout(timeoutId);
    if (typeof wait !== 'number' || Number.isNaN(wait)) {
      try {
        return Promise.resolve<ReturnType<F>>(func(...args));
      } catch (error) {
        return Promise.reject(error);
      }
    } else {
      return new Promise<ReturnType<F>>((resolve, reject) => {
        timeoutId = window.setTimeout(() => {
          try {
            resolve(func(...args));
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

  debounced.restore = () => func;

  return debounced;
};

type FunctionType<A extends any[] = [], R = void> = (...args: A) => R;
type AnyFunction = FunctionType<any, any>;

/** A function that has been debounced. */
export type DebouncedFunction<F extends AnyFunction> = {
  (...args: Parameters<F>): Promise<ReturnType<F>>;
  cancel(): void;
  restore(): F;
};

/** A function that can be debounced. */
export type DebouncibleFunction<F extends AnyFunction> =
  | DebouncedFunction<F>
  | F;
