import { createAction } from '../../../../utils/actions';

import { ADMIN_API } from '../../../../config/wagtailConfig';

function getHeaders() {
  const headers = new Headers();
  headers.append('Content-Type', 'application/json');

  // Need this header in order for Wagtail to recognise the request as AJAX.
  // This causes it to return 403 responses for authentication errors (rather than redirecting)
  headers.append('X-Requested-With', 'XMLHttpRequest');

  return {
    credentials: 'same-origin',
    headers: headers,
    method: 'GET',
  };
}

function get(url) {
  return fetch(url, getHeaders()).then((response) => {
    switch (response.status) {
    case 200:
      return response.json();
    case 400:
      return response.json().then((json) => Promise.reject(`API Error: ${json.message}`));
    case 403:
      return Promise.reject('You haven\'t got permission to view this. Please log in again.');
    case 500:
      return Promise.reject('Internal server error');
    default:
      return Promise.reject(`Unrecognised status code: ${response.statusText} (${response.status})`);
    }
  });
}


export const setView = createAction('SET_VIEW', (viewName, viewOptions) => ({ viewName, viewOptions }));

export const fetchPagesStart = createAction('FETCH_START');
export const fetchPagesSuccess = createAction('FETCH_SUCCESS', (itemsJson, parentJson) => ({ itemsJson, parentJson }));
export const fetchPagesFailure = createAction('FETCH_FAILURE', message => ({ message }));


export function browse(parentPageID, pageNumber) {
  // HACK: Assuming page 1 is the root page
  // eslint-disable-next-line no-param-reassign
  if (parentPageID === 1) { parentPageID = 'root'; }

  return (dispatch) => {
    dispatch(fetchPagesStart());

    const limit = 20;
    const offset = (pageNumber - 1) * limit;
    // eslint-disable-next-line max-len
    const itemsUrl = `${ADMIN_API.PAGES}?child_of=${parentPageID}&fields=parent,children&limit=${limit}&offset=${offset}`;
    const parentUrl = `${ADMIN_API.PAGES}${parentPageID}/?fields=ancestors`;

    // HACK: The admin API currently doesn't serve the root page
    if (parentPageID === 'root') {
      return get(itemsUrl)
        .then((itemsJson) => {
          dispatch(setView('browse', { parentPageID, pageNumber }));
          dispatch(fetchPagesSuccess(itemsJson, null));
        }).catch((error) => {
          dispatch(fetchPagesFailure(error));
        });
    }

    return Promise.all([get(itemsUrl), get(parentUrl)])
      .then(([itemsJson, parentJson]) => {
        dispatch(setView('browse', { parentPageID, pageNumber }));
        dispatch(fetchPagesSuccess(itemsJson, parentJson));
      }).catch((error) => {
        dispatch(fetchPagesFailure(error));
      });
  };
}


export function search(queryString, restrictPageTypes, pageNumber) {
  return (dispatch) => {
    dispatch(fetchPagesStart());

    const limit = 20;
    const offset = (pageNumber - 1) * limit;
    let url = `${ADMIN_API.PAGES}?fields=parent&search=${queryString}&limit=${limit}&offset=${offset}`;

    if (restrictPageTypes != null) {
      url += `&type=${restrictPageTypes.join(',')}`;
    }

    return get(url)
      .then((json) => {
        dispatch(setView('search', { queryString, pageNumber }));
        dispatch(fetchPagesSuccess(json, null));
      }).catch((error) => {
        dispatch(fetchPagesFailure(error));
      });
  };
}
