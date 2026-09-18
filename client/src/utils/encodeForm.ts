/**
 * Encode form fields into a URL query string format.
 *
 * Converts the values of an HTML form into a URL-encoded query string using
 * `FormData` and `URLSearchParams`. Multiple values for the same field name are
 * preserved. File inputs are represented by their filename to match legacy
 * behavior where jQuery's `.serialize()` produced a string payload.
 *
 * Note: If you need to upload file contents, prefer sending the `FormData`
 * directly with `fetch` rather than using this helper.
 *
 * @param form - The HTML form element to serialize.
 * @returns A URL-encoded query string representing the form data.
 * @see https://developer.mozilla.org/docs/Web/API/FormData
 * @see https://developer.mozilla.org/docs/Web/API/URLSearchParams
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
