interface MessageWithOrigin {
  // Include the origin so the preview panel knows to use the correct origin,
  // which may not be the same as the iframe's src (e.g. due to a redirect).
  origin: string;
}

export interface AxeReady {
  type: 'w-userbar:axe-ready';
}

export interface RequestScroll extends MessageWithOrigin {
  type: 'w-preview:request-scroll';
}

export interface GetScrollPosition {
  type: 'w-preview:get-scroll-position';
}

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

export function getWagtailMessage(event: MessageEvent): WagtailMessage | null {
  if (
    !(
      event.type === 'message' &&
      typeof event.data === 'object' &&
      'wagtail' in event.data
    )
  )
    return null;

  return event.data.wagtail;
}
