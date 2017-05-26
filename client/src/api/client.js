const fetch = global.fetch;
const Headers = global.Headers;

const REQUEST_TIMEOUT = 15000;

const checkStatus = (response) =>  {
  if (response.status >= 200 && response.status < 300) {
    return response;
  }

  const error = new Error(response.statusText);

  throw error;
};

const parseJSON = response => response.json();

// Response timeout cancelling the promise (not the request).
// See https://github.com/github/fetch/issues/175#issuecomment-216791333.
const timeout = (ms, promise) => {
  const race = new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error('Response timeout'));
    }, ms);

    promise.then((res) => {
      clearTimeout(timeoutId);
      resolve(res);
    }, (err) => {
      clearTimeout(timeoutId);
      reject(err);
    });
  });

  return race;
};

/**
 * Wrapper around fetch with sane defaults for behavior in the face of
 * errors.
 */
const request = (method, url) => {
  const options = {
    credentials: 'same-origin',
    headers: new Headers({
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    }),
    method: method
  };

  return timeout(REQUEST_TIMEOUT, fetch(url, options))
    .then(checkStatus)
    .then(parseJSON);
};

export const get = url => request('GET', url);
