/**
 * Encodes form data into a URL-encoded string (application/x-www-form-urlencoded).
 * Replacement for jQuery's $(form).serialize()
 */
export function encodeForm(form: HTMLFormElement): string {
  const formData = new FormData(form);
  const params = new URLSearchParams();

  Array.from(formData.entries()).forEach(([key, value]) => {
    const valueString =
      typeof value === 'string' ? value : (value as File)?.name || '';
    params.append(key, valueString);
  });

  return params.toString();
}
