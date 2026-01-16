/**
 * Image URL Upload - Main JavaScript
 *
 * Handles dynamic URL field management and batch image uploading
 * for the Wagtail Image URL Upload plugin.
 *
 * @version 0.1.0
 */

document.addEventListener('DOMContentLoaded', function () {
  // State
  let urlFieldCounter = 1;
  let isUploading = false;

  /**
   * Create a new URL input field
   * @param {number} number - The field number for labeling
   * @returns {HTMLElement} The created field element
   */
  function createUrlField(number) {
    const fieldHtml = `
      <div class="url-field-group w-flex w-items-start w-gap-3 w-p-4 w-rounded-lg w-transition-all hover:w-border-primary-300">
        <div class="w-flex-1">
          <label class="w-block w-text-sm w-font-medium w-text-grey-700 w-mb-2">
            Image URL #<span class="url-number">${number}</span>
          </label>
          <input
            type="url"
            class="url-input w-w-full w-px-4 w-py-2 w-border w-border-grey-300 w-rounded-md focus:w-ring-2 focus:w-ring-primary-500 focus:w-border-primary-500 w-transition-all w-bg-transparent"
            placeholder="https://example.com/image.jpg"
            aria-label="Image URL ${number}"
          />
        </div>
        <button
          type="button"
          class="remove-url-btn w-mt-8 w-p-2 w-text-critical-600 hover:w-bg-critical-50 w-rounded-md w-transition-colors"
          title="Remove this URL"
          aria-label="Remove URL field ${number}"
        >
          <svg class="w-w-5 w-h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </button>
        <!-- Inline Status Display -->
        <div class="url-status w-hidden w-mt-8 w-items-center w-gap-2" role="status" aria-live="polite">
          <div class="status-icon"></div>
          <span class="status-text w-text-sm"></span>
        </div>
      </div>
    `;
    // Create a temporary container and return the first child
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = fieldHtml.trim();
    return tempDiv.firstElementChild;
  }

  /**
   * Update numbering of all URL fields
   */
  function updateFieldNumbers() {
    const fieldGroups = document.querySelectorAll(
      '#url-fields-container .url-field-group',
    );
    fieldGroups.forEach((fieldGroup, index) => {
      const urlNumber = fieldGroup.querySelector('.url-number');
      const urlInput = fieldGroup.querySelector('.url-input');
      if (urlNumber) {
        urlNumber.textContent = String(index + 1);
      }
      if (urlInput) {
        urlInput.setAttribute('aria-label', `Image URL ${index + 1}`);
      }
    });
  }

  /**
   * Update inline status for a URL field
   * @param {HTMLElement} fieldGroup - The field group element
   * @param {string} status - Status type (uploading, success, error, duplicate)
   * @param {string} message - Status message to display
   */
  function updateInlineStatus(fieldGroup, status, message) {
    const statusDiv = fieldGroup.querySelector('.url-status');
    const statusIcon = statusDiv.querySelector('.status-icon');
    const statusText = statusDiv.querySelector('.status-text');

    statusDiv.classList.remove('w-hidden');
    statusText.textContent = message || '';

    // Reset all border colors
    fieldGroup.classList.remove(
      'w-border-grey-200',
      'w-border-positive-300',
      'w-border-critical-300',
      'w-border-warning-300',
      'w-border-primary-300',
    );

    // Update based on status
    const statusConfig = {
      uploading: {
        borderClass: 'w-border-primary-300',
        textClass: ['w-text-primary-700'],
        icon: `
          <svg class="w-animate-spin w-w-5 w-h-5 w-text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        `,
      },
      success: {
        borderClass: 'w-border-positive-300',
        textClass: ['w-text-positive-700', 'w-font-medium'],
        icon: `
          <svg class="w-w-5 w-h-5 w-text-positive-600" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
        `,
      },
      error: {
        borderClass: 'w-border-critical-300',
        textClass: ['w-text-critical-700', 'w-font-medium'],
        icon: `
          <svg class="w-w-5 w-h-5 w-text-critical-600" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        `,
      },
      duplicate: {
        borderClass: 'w-border-warning-300',
        textClass: ['w-text-warning-700', 'w-font-medium'],
        icon: `
          <svg class="w-w-5 w-h-5 w-text-warning-600" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        `,
      },
    };

    const config = statusConfig[status];
    if (config) {
      fieldGroup.classList.add(config.borderClass);
      statusIcon.innerHTML = config.icon;
      statusText.classList.remove(
        'w-text-primary-700',
        'w-text-positive-700,',
        'w-text-critical-700',
        'w-text-warning-700',
      );
      statusText.classList.add(...config.textClass);
    }
  }

  /**
   * Validate URL format
   * @param {string} url - The URL to validate
   * @returns {boolean} True if valid
   */
  function isValidUrl(url) {
    try {
      const urlObj = new URL(url);
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  }

  /**
   * Slide up animation (jQuery slideUp equivalent)
   * @param {HTMLElement} element - Element to animate
   * @param {number} duration - Animation duration in milliseconds
   * @param {function} callback - Callback function to run after animation
   */
  function slideUp(element, duration, callback) {
    element.style.transitionProperty = 'height, margin, padding';
    element.style.transitionDuration = `${duration}ms`;
    element.style.boxSizing = 'border-box';
    element.style.offsetHeight = `${element.offsetHeight}px`;
    element.style.overflow = 'hidden';

    requestAnimationFrame(() => {
      element.style.height = '0';
      element.style.paddingTop = '0';
      element.style.paddingBottom = '0';
      element.style.marginTop = '0';
      element.style.marginBottom = '0';
    });

    setTimeout(() => {
      element.remove();
      if (callback) callback();
    }, duration);
  }

  /**
   * Make HTTP request
   * @param {string} url - URL to fetch
   * @param {object} [options] - Fetch options
   * @returns {Promise<Response>} - Promise that resolves with response data
   */
  async function makeRequest(url, options = {}) {
    const defaultOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Requested-With': 'XMLHttpRequest',
      },
    };

    const mergedOptions = { ...defaultOptions, ...options };

    if (mergedOptions.data && mergedOptions.method === 'POST') {
      const formData = new URLSearchParams();
      Object.keys(mergedOptions.data).forEach((key) => {
        formData.append(key, mergedOptions.data[key]);
      });
      mergedOptions.body = formData;
      delete mergedOptions.data;
    }

    const response = await fetch(url, mergedOptions);
    if (!response.ok) {
      throw new Error(response.statusText);
    }
    return response;
  }

  /**
   * Promise.all equivalent for handling multiple requests
   * @param {Array} promises - Array of promises
   * @returns {Promise} Promise that resolves when all complete
   */
  function whenAllComplete(promises) {
    return Promise.allSettled(promises);
  }

  /**
   * Initialize the plugin
   */
  /**
   * Initialize the plugin
   */
  function init() {
    // Add URL field button
    const addButton = document.getElementById('add-url-field-btn');
    if (addButton) {
      addButton.addEventListener('click', function () {
        if (isUploading) {
          return; // Prevent adding fields during upload
        }

        urlFieldCounter += 1;
        const newField = createUrlField(urlFieldCounter);

        // Use requestAnimationFrame to prevent visible glitch
        requestAnimationFrame(() => {
          const container = document.getElementById('url-fields-container');
          if (container) {
            container.appendChild(newField);
            const urlInput = newField.querySelector('.url-input');
            if (urlInput) {
              urlInput.focus();
            }
          }
        });
      });
    }

    // Remove URL field (delegated event)
    document.addEventListener('click', function (e) {
      const deleteButton = e.target.closest('.remove-url-btn');
      if (e.target && deleteButton) {
        if (isUploading) {
          return; // Prevent removing fields during upload
        }
        const fieldGroup = deleteButton.closest('.url-field-group');
        const fieldsCount = document.querySelectorAll(
          '#url-fields-container .url-field-group',
        ).length;

        if (fieldsCount <= 1) {
          alert('You must keep at least one URL field.');
          return;
        }

        slideUp(fieldGroup, 300, function () {
          updateFieldNumbers();
        });
      }
    });

    // Fetch URLs button handler
    const fetchButton = document.getElementById('fetch-urls-button');
    if (fetchButton) {
      fetchButton.addEventListener('click', function (e) {
        e.preventDefault();

        if (isUploading) {
          return;
        }

        const uploadUrl = this.dataset.url;

        // Collect all URL fields with their values
        const urlFields = [];
        const fieldGroups = document.querySelectorAll('.url-field-group');

        fieldGroups.forEach((fieldGroup) => {
          const urlInput = fieldGroup.querySelector('.url-input');
          const url = urlInput ? urlInput.value.trim() : '';

          if (url) {
            if (!isValidUrl(url)) {
              updateInlineStatus(fieldGroup, 'error', '✗ Invalid URL format');
              return;
            }
            urlFields.push({ fieldGroup, url });
          }
        });

        // Validate that we have at least one URL
        if (urlFields.length === 0) {
          alert('Please enter at least one valid URL.');
          return;
        }

        // Set uploading state
        isUploading = true;
        this.disabled = true;

        const buttonText = this.querySelector('.button-text');
        const buttonLoading = this.querySelector('.button-loading');
        if (buttonText) buttonText.classList.add('w-hidden');
        if (buttonLoading) buttonLoading.classList.remove('w-hidden');

        // Upload all URLs and track results
        const uploadResults = [];
        const requests = urlFields.map(async ({ fieldGroup, url }) => {
          // Show uploading status
          updateInlineStatus(fieldGroup, 'uploading', 'Uploading...');

          const postData = {
            url: url,
          };

          // Get CSRF token
          const csrfInput = document.querySelector(
            'input[name="csrfmiddlewaretoken"]',
          );
          if (csrfInput) {
            postData.csrfmiddlewaretoken = csrfInput.value;
          }

          // Get collection if exists
          const collectionSelect = document.querySelector(
            'select[name="collection"]',
          );
          if (collectionSelect) {
            postData.collection = collectionSelect.value;
          }

          try {
            const response = await makeRequest(uploadUrl, {
              method: 'POST',
              data: postData,
            });
            const result = await response.json();
            if (result.success) {
              if (result.duplicate) {
                updateInlineStatus(
                  fieldGroup,
                  'duplicate',
                  '⚠️ Already exists',
                );
                uploadResults.push({ success: true, duplicate: true });
              } else {
                updateInlineStatus(
                  fieldGroup,
                  'success',
                  '✓ Uploaded successfully',
                );
                uploadResults.push({ success: true, duplicate: false });
              }
            } else {
              updateInlineStatus(
                fieldGroup,
                'error',
                '✗ ' + (response.statusText || 'Upload failed'),
              );
              uploadResults.push({ success: false });
            }
          } catch (error) {
            const errorMsg = error.message || 'Network error';
            updateInlineStatus(fieldGroup, 'error', `✗ Error: ${errorMsg}`);
            uploadResults.push({ success: false });
          }
        });
        // When all requests complete, re-enable the button and check for redirect
        whenAllComplete(requests).then(() => {
          isUploading = false;
          fetchButton.disabled = false;

          if (buttonText) buttonText.classList.remove('w-hidden');
          if (buttonLoading) buttonLoading.classList.add('w-hidden');

          // Check if all uploads were successful (including duplicates)
          const allSuccessful = uploadResults.every((result) => result.success);
          const hasNewImages = uploadResults.some(
            (result) => result.success && !result.duplicate,
          );

          // Redirect to the gallery if all were successful and at least one new image was added
          if (allSuccessful && hasNewImages) {
            // Show a brief success message before redirecting
            setTimeout(() => {
              window.location.href = '/admin/images/';
            }, 1000);
          }
        });
      });
    }
  }

  // Initialize when DOM is ready
  init();
});
