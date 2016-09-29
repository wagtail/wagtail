import { createAction } from 'redux-actions';

import { API_PAGES, PAGES_ROOT_ID } from '../../../../config';


function getHeaders() {
  const headers = new Headers();
  headers.append('Content-Type', 'application/json');

  // Need this header in order for Wagtail to recognise the request as AJAX.
  // This causes it to return 403 responses for authentication errors (rather than redirecting)
  headers.append('X-Requested-With', 'XMLHttpRequest');

  return {
    credentials: 'same-origin',
    headers: headers,
    method: 'GET'
  };
}

function get(url) {
  return fetch(url, getHeaders()).then(response => {
    switch (response.status) {
      case 200:  // OK
        return response.json();
      case 400:  // Bad request
        return response.json().then(json => {
          return Promise.reject("API Error: " + json.message);
        });
      case 403:  // Forbidden
        return Promise.reject("You haven't got permission to view this. Please log in again.");
      case 500:  // Internal server error
        return Promise.reject("Internal server error");
      default:   // Unrecognised status
        return Promise.reject(`Unrecognised status code: ${response.statusText} (${response.status})`);
    }
  });
}


export const setView = createAction('SET_VIEW', (viewName, viewOptions) => ({ viewName, viewOptions }));

export const fetchPagesStart = createAction('FETCH_START');
export const fetchPagesSuccess = createAction('FETCH_SUCCESS', (itemsJson, parentJson) => ({ itemsJson, parentJson }));
export const fetchPagesFailure = createAction('FETCH_FAILURE', (message) => ({ message }));


export function browse(parentPageID, pageNumber) {
  // HACK: Assuming page 1 is the root page
  if (parentPageID == 1) { parentPageID = 'root'; }

  return (dispatch, getState) => {
    dispatch(fetchPagesStart());

    let limit = 20;
    let offset = (pageNumber - 1) * limit;
    let itemsUrl = `${API_PAGES}?child_of=${parentPageID}&fields=parent,children&limit=${limit}&offset=${offset}`;
    let parentUrl = `${API_PAGES}${parentPageID}/?fields=ancestors`;

    // HACK: The admin API currently doesn't serve the root page
    if (parentPageID == 'root') {
      return get(itemsUrl)
        .then(itemsJson => {
          dispatch(setView('browse', { parentPageID, pageNumber }));
          dispatch(fetchPagesSuccess(itemsJson, null));
        }).catch((error) => {
          console.error(error);
          dispatch(fetchPagesFailure(error));
        });
    }

    return Promise.all([get(itemsUrl), get(parentUrl)])
      .then(([itemsJson, parentJson]) => {
        dispatch(setView('browse', { parentPageID, pageNumber }));
        dispatch(fetchPagesSuccess(itemsJson, parentJson));
      }).catch((error) => {
        console.error(error);
        dispatch(fetchPagesFailure(error));
      });
  };
}


export function search(queryString, restrictPageTypes, pageNumber) {
  return (dispatch, getState) => {
    dispatch(fetchPagesStart());

    let limit = 20;
    let offset = (pageNumber - 1) * limit;
    let url = `${API_PAGES}?fields=parent&search=${queryString}&limit=${limit}&offset=${offset}`;

    if (restrictPageTypes != null) {
      url += '&type=' + restrictPageTypes.join(',');
    }

    return get(url)
      .then(json => {
        dispatch(setView('search', { queryString, pageNumber }));
        dispatch(fetchPagesSuccess(json, null));
      }).catch((error) => {
        console.error(error);
        dispatch(fetchPagesFailure(error));
      });
  };
}
