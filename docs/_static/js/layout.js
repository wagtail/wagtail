/**
         * Get version of the currently served docs.
         *
         * PR builds have their version set to the PR ID (for example "6753").
         * If the docs are built for a PR, use the "latest" search index.
         * Otherwise, use the search index for the current version.
         */
function getReadTheDocsVersion() {
    const RTD_VERSION = (window.READTHEDOCS_DATA || {}).version || 'latest'
    const version = RTD_VERSION.match(/^\d+$/) ? 'latest' : RTD_VERSION
    return version
}

export function getVersionFacetFilter() {
    return `version:${getReadTheDocsVersion()}`;
}

/**
 * Return true (debug: on) for local builds or Read the Docs PR previews.
 *
 * The debug mode allows inspection of the dropodown.
 */
function getSearchDebugMode() {
    let debug = false
    if (window.READTHEDOCS_DATA === undefined) {
        // When developing locally, the `window.READTHEDOCS_DATA` object does not exist.
        debug = true
    } else {
        // When PR preview on Readthedocs, then the version can be converted into
        // a number. This does not work for the production version identifiers
        // like 'stable', 'latest', 'v2.12', etc. In that case `Number()` is `NaN`.
        const versionNumber = Number(window.READTHEDOCS_DATA.version)
        debug = !Number.isNaN(versionNumber)
    }
    return debug
}

export default function docSearchReady() {
    /**
     * Configure Algolia DocSearch.
     * See https://github.com/algolia/docsearch-configs/blob/master/configs/wagtail.json for index configuration.
     */
    const search = docsearch({ // eslint-disable-line
        apiKey: '8325c57d16798633e29d211c26c7b6f9',
        indexName: 'wagtail',
        inputSelector: '#searchbox [name="q"]',
        algoliaOptions: {
            facetFilters: [getVersionFacetFilter()],
        },
        autocompleteOptions: {
            // Do NOT automatically select the first suggestion in the dropdown.
            // https://github.com/algolia/autocomplete/blob/45fa32d008620cf52bf4a90530be338543dfba7f/README.md#global-options
            autoSelect: false
        },
        debug: getSearchDebugMode(),
    })

    // Change page styles when the dropdown is open, to lock scrolling.
    search.autocomplete.on('autocomplete:updated',(event) => {
        const isOpen = event.target.value.trim() !== '';
        document.body.classList.toggle('body--autocomplete-open', isOpen);
    });
    search.autocomplete.on('autocomplete:closed', () => {
        document.body.classList.toggle('body--autocomplete-open', false);
    });
    return search
}

docSearchReady();