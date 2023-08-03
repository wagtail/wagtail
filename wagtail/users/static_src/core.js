// Load the Wagtail version from the window variable
const staticWagtailVersion = window.STATIC_WAGTAIL_VERSION;

// Load the runtime version from the Django context or a global variable if provided
const runtimeWagtailVersion = '{% if wagtail_version %}{% autoescape off %}{{ wagtail_version }}{% endautoescape %}{% else %}{{ STATIC_WAGTAIL_VERSION }}{% endif %}';

// Compare the versions
if (staticWagtailVersion && runtimeWagtailVersion && staticWagtailVersion !== runtimeWagtailVersion) {
  console.log(`Warning: The Wagtail version (${runtimeWagtailVersion}) does not match the static file version (${staticWagtailVersion}). Please check if the static files are up to date.`);
}
