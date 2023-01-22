/**
 * Get version of the currently served docs.
 *
 * PR builds have their version set to the PR ID (for example "6753").
 * If the docs are built for a PR, use the "latest" search index.
 * Otherwise, use the search index for the current version.
 */
function getReadTheDocsVersion() {
  const RTD_VERSION = (window.READTHEDOCS_DATA || {}).version || 'latest';
  const version = RTD_VERSION.match(/^\d+$/) ? 'latest' : RTD_VERSION;
  return version;
}

function getVersionFacetFilter() {
  return `version:${getReadTheDocsVersion()}`;
}

/**
 * Return true (debug: on) for local builds or Read the Docs PR previews.
 *
 * The debug mode allows inspection of the dropodown.
 */
function getSearchDebugMode() {
  let debug = false;
  if (window.READTHEDOCS_DATA === undefined) {
    // When developing locally, the `window.READTHEDOCS_DATA` object does not exist.
    debug = true;
  } else {
    // When PR preview on Readthedocs, then the version can be converted into
    // a number. This does not work for the production version identifiers
    // like 'stable', 'latest', 'v2.12', etc. In that case `Number()` is `NaN`.
    const versionNumber = Number(window.READTHEDOCS_DATA.version);
    debug = !Number.isNaN(versionNumber);
  }
  return debug;
}
/**
 * Configure Algolia DocSearch.
 * See https://github.com/algolia/docsearch-configs/blob/master/configs/wagtail.json for index configuration.
 */
function docSearchReady() {
  try {
    const search = window.docsearch({
      apiKey: '8325c57d16798633e29d211c26c7b6f9',
      indexName: 'wagtail',
      inputSelector: '#searchbox [name="q"]',
      algoliaOptions: {
        facetFilters: [getVersionFacetFilter()],
      },
      autocompleteOptions: {
        // Do NOT automatically select the first suggestion in the dropdown.
        // https://github.com/algolia/autocomplete/blob/45fa32d008620cf52bf4a90530be338543dfba7f/README.md#global-options
        autoSelect: false,
      },
      debug: getSearchDebugMode(),
    });

    // Change page styles when the dropdown is open, to lock scrolling.
    search.autocomplete.on('autocomplete:updated', (event) => {
      const isOpen = event.target.value.trim() !== '';
      document.body.classList.toggle('body--autocomplete-open', isOpen);
    });
    search.autocomplete.on('autocomplete:closed', () => {
      document.body.classList.toggle('body--autocomplete-open', false);
    });
    return search;
  } catch (err) {
    return null;
  }
}

docSearchReady();

function setStartEndForPaginator(
  currentPage,
  totalPages,
  nbPagesLinkToDisplay,
) {
  let start = 0;
  let end = totalPages;

  if (totalPages > nbPagesLinkToDisplay) {
    start = currentPage;

    if (totalPages - currentPage < nbPagesLinkToDisplay) {
      start = totalPages - nbPagesLinkToDisplay;
    }

    if (totalPages - start > nbPagesLinkToDisplay) {
      end = currentPage + nbPagesLinkToDisplay;
    }
  }

  return [start, end];
}

function addHeadingForQuery(query, parentElement) {
  const searchHeading = document.createElement('h1');
  searchHeading.textContent = `Search results for “${query}”`;
  parentElement.appendChild(searchHeading);
}

function createHitElement(hitData, query) {
  const pageURL = new URL(hitData.url);
  pageURL.hash = '';
  pageURL.searchParams.set('highlight', query);
  const anchorURL = new URL(hitData.url);
  anchorURL.searchParams.set('highlight', query);
  const result = hitData._highlightResult; // eslint-disable-line

  const hitListElement = document.createElement('li');

  const hierarchies = Object.values(result.hierarchy);
  const firstHierarchyLevel = hierarchies[0];
  const lastHierarchyLevel = hierarchies[hierarchies.length - 1];

  const pageLink = document.createElement('a');
  hitListElement.appendChild(pageLink);
  pageLink.innerHTML = firstHierarchyLevel.value;
  pageLink.href = pageURL;

  const contextElement = document.createElement('div');
  hitListElement.appendChild(contextElement);
  contextElement.className = 'context';

  if (lastHierarchyLevel && lastHierarchyLevel !== firstHierarchyLevel) {
    const contextLinkContainer = document.createElement('div');
    contextElement.appendChild(contextLinkContainer);
    const contextLink = document.createElement('a');
    contextLinkContainer.appendChild(contextLink);
    contextLink.innerHTML = lastHierarchyLevel.value;
    contextLink.href = anchorURL;
  }

  if (result.content) {
    const contentElement = document.createElement('div');
    contentElement.innerHTML = result.content.value;
    contextElement.appendChild(contentElement);
  }

  return hitListElement;
}

function addResultsList(hits, query, parentElement) {
  const searchResultsList = document.createElement('ul');
  searchResultsList.className = 'search';
  hits.forEach((hit) => {
    const hitElement = createHitElement(hit, query);
    searchResultsList.appendChild(hitElement);
  });
  parentElement.appendChild(searchResultsList);
}

function runSearchPageSearch(page) {
  const urlParams = new URLSearchParams(window.location.search);
  const query = urlParams.get('q');

  const searchResultsContainer = document.getElementById('search-results');

  // Erase previous results

  if (searchResultsContainer) {
    searchResultsContainer.innerHTML = '';
    document.querySelector('.pagination-list').innerHTML = '';
    addHeadingForQuery(query, searchResultsContainer);
  }

  const docSearch = docSearchReady();
  const index = docSearch.client.initIndex('wagtail');

  index
    .search(query, {
      hitsPerPage: 100,
      page: page,
      facetFilters: [getVersionFacetFilter()],
    })
    .then((result) => {
      // Display pagination if more than 1 page returned
      const { nbPages } = result;
      if (nbPages > 1) {
        document.querySelector('#pagination').hidden = false;
        window.displayPagination(page, nbPages);
      }

      // Display hits
      const { hits } = result;
      addResultsList(hits, query, searchResultsContainer);
    })
    .catch((error) => console.log(error)); // eslint-disable-line
}

function runPreviousPage() {
  const currentPage = Number(
    document.querySelector('#pagination > ul > li > button').ariaCurrent,
  );
  runSearchPageSearch(currentPage - 1);
}

function runNextPage() {
  const currentPage = Number(
    document.querySelector('#pagination > ul > li > button').ariaCurrent,
  );
  runSearchPageSearch(currentPage + 1);
}
// eslint-disable-next-line
function displayPagination(page, totalPages) {
  const pagination = document.querySelector('#pagination');
  const paginationList = pagination.querySelector('.pagination-list');

  pagination.querySelector('.pagination-previous').hidden = false;
  pagination.querySelector('.pagination-previous').hidden = page === 0;
  pagination.querySelector('.pagination-next').hidden = page === totalPages - 1;

  const toBeDisplayed = 7;
  const [start, end] = setStartEndForPaginator(page, totalPages, toBeDisplayed);

  for (let i = start; i < end; i += 1) {
    const newPaginationItem = document.createElement('li');
    const newPaginationbutton = document.createElement('button');
    newPaginationbutton.classList.add('pagination-button');
    newPaginationbutton.innerHTML = 'Page ' + (i + 1) + ' of ' + end;
    let flag = false;
    if (i === page) {
      newPaginationbutton.setAttribute('aria-label', `page ${i + 1}`);
      newPaginationbutton.setAttribute('aria-current', `${i}`);
      flag = true;
    }

    // Register event listeners
    newPaginationbutton.addEventListener('click', () => {
      runSearchPageSearch(page);
    });

    if (flag === true) {
      if (page > 0) {
        pagination
          .querySelector('[data-pagination-previous]')
          .removeEventListener('click', runPreviousPage);
        pagination
          .querySelector('[data-pagination-next]')
          .removeEventListener('click', runNextPage);
      }
      pagination
        .querySelector('[data-pagination-previous]')
        .addEventListener('click', runPreviousPage);
      pagination
        .querySelector('[data-pagination-next]')
        .addEventListener('click', runNextPage);
    }

    const currentButton = document.querySelector(
      '#pagination > ul > li >button',
    );
    const currentList = document.querySelector('#pagination > ul > li');
    if (currentButton && flag === true) {
      paginationList.replaceChild(newPaginationItem, currentList);
      newPaginationItem.append(newPaginationbutton);
      currentButton.remove();
    } else if (!currentButton && flag === true) {
      newPaginationItem.append(newPaginationbutton);
      paginationList.append(newPaginationItem);
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  runSearchPageSearch(0);
});
