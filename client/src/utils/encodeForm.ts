/**
 * Encodes form data into a URL-encoded string (application/x-www-form-urlencoded).
 * Replacement for jQuery's $(form).serialize()
 */
export function encodeForm(form: HTMLFormElement): string {
  const formData = new FormData(form);
  const params = new URLSearchParams();

  formData.forEach((value, key) => {
    if (typeof value === 'string') params.append(key, value);
  });

  return params.toString();
}
