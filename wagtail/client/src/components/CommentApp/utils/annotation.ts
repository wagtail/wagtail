export interface Annotation {
  getTab(): string | null | undefined;
  getAnchorNode(focused: boolean): Element;
}
