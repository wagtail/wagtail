/**
 * Encodes form data into a URL-encoded string (application/x-www-form-urlencoded).
 * Replacement for jQuery's $(form).serialize()
 */
export const encodeForm = (form: HTMLFormElement): string => {
  const formData = new FormData(form);
  return new URLSearchParams(formData as any).toString();
};
