export interface Annotation {
  getTab(): string | null | undefined;
  getDesiredPosition(focused: boolean): number;
}
