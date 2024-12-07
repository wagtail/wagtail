/**
 * Returns a promise that will resolve after either the animation, transition
 * or the max delay of time is reached.
 *
 * If `maxDelay` is provided as zero or a falsy value, the promise resolve immediately.
 */
export const transition = (element: HTMLElement, { maxDelay = 350 } = {}) =>
  new Promise<AnimationEvent | TransitionEvent | null>((resolve) => {
    if (!maxDelay || maxDelay <= 0) {
      resolve(null);
      return;
    }

    let timer: number | undefined;

    const finish = (event: AnimationEvent | TransitionEvent | null) => {
      if (event && event.target !== element) return;
      window.clearTimeout(timer);
      element.removeEventListener('transitionend', finish);
      element.removeEventListener('animationend', finish);
      resolve(event || null);
    };

    element.addEventListener('animationend', finish);
    element.addEventListener('transitionend', finish);
    timer = window.setTimeout(finish, maxDelay);
  });
