import _ from 'lodash';

const fetch = global.fetch;

// fetch wrapper for JSON APIs.
export const get = (url) => {
  const headers = new Headers({
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  });

  const options = {
    credentials: 'same-origin',
    headers: headers,
    method: 'GET'
  };

  return fetch(url, options)
    .then((res) => {
      const response = {
        status: res.status,
        statusText: res.statusText,
        headers: res.headers
      };

      let ret;
      if (response.status >= 200 && response.status < 300) {
        ret = res.json().then(json => _.assign(response, { body: json }));
      } else {
        ret =  res.text().then((text) => {
          const err = _.assign(new Error(response.statusText), response, { body: text });
          throw err;
        });
      }

      return ret;
    });
};
