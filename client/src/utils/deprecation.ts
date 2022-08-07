/**
 * Prepare a function to dispatch a warning event with a specific title.
 *
 * @param title - Warning type in UpperCamelCase
 */
const developerWarning =
  (title: string) =>
  /**
   * Dispatch a warning event.
   *
   * @param message - specific message to this warning
   * @param options
   * @param options.data - optional data object which will be logged to the console
   * @param options.target - optional target DOM element to dispatch the event from
   */
  (
    message: string,
    {
      data = null,
      target = document,
    }: {
      data?: Record<string, unknown> | null;
      target?: EventTarget;
    } = {},
  ): void => {
    target.dispatchEvent(
      new CustomEvent('wagtail:development-warning', {
        bubbles: true,
        cancelable: false,
        detail: { title, message, data },
      }),
    );
  };

export const deprecationWarning = developerWarning('DeprecationWarning');

export const pendingDeprecationWarning = developerWarning(
  'PendingDeprecationWarning',
);

export const removedInWagtail50Warning = developerWarning(
  'RemovedInWagtail50Warning',
);
