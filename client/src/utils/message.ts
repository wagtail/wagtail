/**
 * A message that includes the sender's origin, so the CMS can use the correct
 * origin when responding to the message, without requiring developers to
 * specify the expected origin wherever necessary (e.g. in the userbar).
 */
interface MessageWithOrigin {
  origin: string;
}

/**
 * Indicates Axe in the userbar is ready for another run.
 */
export interface AxeReady {
  type: 'w-userbar:axe-ready';
}

/**
 * Indicates this window (i.e. the new preview iframe) is requesting the target
 * window (i.e. the CMS) to restore the scroll position of a previous window to
 * this window.
 */
export interface RequestScroll extends MessageWithOrigin {
  type: 'w-preview:request-scroll';
}

/**
 * Indicates this window (i.e. the CMS) is requesting the recipient window's
 * (i.e. the old preview iframe) scroll position.
 */
export interface GetScrollPosition {
  type: 'w-preview:get-scroll-position';
}

/**
 * For simplicity, the same message type is used for both purposes instead of
 * creating separate message types. This allows the CMS to pass over the message
 * received from the old iframe to the new iframe as-is.
 *
 * @remarks
 * Indicates two things:
 * 1. The current window (i.e. the old preview iframe) is sending its scroll
 *    position to the recipient window (i.e. CMS).
 * 2. The current window (i.e. the CMS) is instructing the recipient window
 *    (i.e. the new preview iframe) to set its scroll position to the given
 *    coordinates.
 */
export interface SetScrollPosition extends MessageWithOrigin {
  type: 'w-preview:set-scroll-position';
  x: number;
  y: number;
}

export type WagtailMessage =
  | AxeReady
  | RequestScroll
  | GetScrollPosition
  | SetScrollPosition;

/**
 * Parses a message event that may contain a Wagtail message.
 * @param event The message event to check for a Wagtail message.
 * @returns The Wagtail message if it exists, or null if it does not.
 */
export function getWagtailMessage(event: MessageEvent): WagtailMessage | null {
  if (!(event.type === 'message' && event?.data?.wagtail)) return null;

  return event.data.wagtail;
}
