# Client-side components

Wagtail's admin interface uses [Stimulus](https://stimulus.hotwired.dev/) to add interactivity to the UI. We provide a set of reusable controllers that can be used in your own customizations or when extending Wagtail.

This guide covers the most common controllers and how to use them.

(w-clipboard)=

## Clipboard `w-clipboard`

**Purpose**: Adds the ability for an element to copy a value to the clipboard.

**Basic Usage**:

```html
<div data-controller="w-clipboard">
    <input type="text" value="Hello World" data-w-clipboard-target="value" />
    <button type="button" data-action="w-clipboard#copy">Copy</button>
</div>
```

**API Reference**: {controller}`w-clipboard`

**Accessibility**:
- Ensure the button has a recognizable label (e.g. "Copy").
- The controller dispatches `w-clipboard:copied` and `w-clipboard:error` events which can be used to show feedback (e.g. a toast message) to screen reader users.

**Limitations**:
- Requires the [Clipboard API](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API) which is supported in all modern browsers but requires a secure context (HTTPS) for write access in some browsers.

(w-dialog)=

## Dialog `w-dialog`

**Purpose**: Manages accessible modal dialogs using [a11y-dialog](https://a11y-dialog.netlify.app/).

**Basic Usage**:

```html
<div
    id="my-dialog"
    data-controller="w-dialog"
    data-w-dialog-theme-value="floating"
    aria-hidden="true"
>
    <!-- Overlay -->
    <div data-a11y-dialog-hide></div>
    <!-- Dialog window -->
    <div role="dialog" aria-labelledby="dialog-title">
        <h1 id="dialog-title">My Dialog</h1>
        <div data-w-dialog-target="body">
            <p>Dialog content</p>
        </div>
        <button type="button" data-action="w-dialog#hide">Close</button>
    </div>
</div>

<button type="button" data-a11y-dialog-show="my-dialog">Open Dialog</button>
```

**API Reference**: {controller}`w-dialog`

**Accessibility**:
- Manages focus trapping and restoration automatically.
- Ensure unique IDs for titles/descriptions linked via `aria-labelledby` / `aria-describedby`.

**Limitations**:
- Wraps `a11y-dialog`; refer to its documentation for advanced usage.

(w-tooltip)=

## Tooltip `w-tooltip`

**Purpose**: Displays a tooltip or popover using [Tippy.js](https://atomiks.github.io/tippyjs/).

**Basic Usage**:

```html
<button
    type="button"
    data-controller="w-tooltip"
    data-w-tooltip-content-value="More detail here"
>
    Hover me
</button>
```

**API Reference**: {controller}`w-tooltip`

**Accessibility**:
- Tooltips triggered by hover/focus are generally accessible if they contain supplementary info.
- Escape key automatically hides the tooltip (via `hideTooltipOnEsc` plugin).

**Limitations**:
- Wraps Tippy.js with a subset of configuration.
- For complex content, use `data-w-tooltip-target="content"` to use an existing DOM element as content.

(w-reveal)=

## Reveal `w-reveal`

**Purpose**: Toggles the visibility of content (collapsible/expandable sections) with ARIA support and optional persistence.

**Basic Usage**:

```html
<section data-controller="w-reveal">
    <button
        type="button"
        data-action="w-reveal#toggle"
        data-w-reveal-target="toggle"
        aria-controls="content-1"
        aria-expanded="false"
    >
        Toggle
    </button>
    <div id="content-1" data-w-reveal-target="content" hidden>
        Hidden content
    </div>
</section>
```

**API Reference**: {controller}`w-reveal`

**Accessibility**:
- Automatically updates `aria-expanded` on toggle buttons.
- Connects buttons to content via `aria-controls`.

**Limitations**:
- Ensure uniqueness of IDs if using multiple reveal controllers.

(w-slug)=

## Slug `w-slug` (or `w-clean`)

**Purpose**: Automatically formats input values (e.g. slugifying titles).

**Basic Usage**:

```html
<input
    type="text"
    name="slug"
    data-controller="w-slug"
    data-action="blur->w-slug#slugify"
>
<!-- Trigger from another field -->
<input
    type="text"
    name="title"
    data-action="blur->w-slug#slugify"
    data-w-slug-target="source" 
    aria-controls="slug-field"
> 
<input
    id="slug-field"
    type="text"
    name="slug"
    data-controller="w-slug"
>
```

**API Reference**: {controller}`w-clean` and {controller}`w-slug`

**Accessibility**:
- Ensure users can review and modify the auto-generated value.

**Limitations**:
- `w-slug` is an alias for `CleanController` but typically implies usage of the `slugify` or `urlify` methods.
- `urlify` supports Unicode and locale-specific rules (mirrors Django's `urlify`).

(w-orderable)=

## Orderable `w-orderable`

**Purpose**: Adds drag-and-drop or manual reordering support using [SortableJS](https://sortablejs.github.io/Sortable/).

**Basic Usage**:

```html
<ul
    data-controller="w-orderable"
    data-w-orderable-url-value="/admin/api/reorder/999999"
    data-w-orderable-message-value="__LABEL__ moved successfully"
>
    <!-- Handle (optional) -->
    <div data-w-orderable-target="handle">Drag</div>

    <li
        data-w-orderable-target="item"
        data-w-orderable-item-id="10"
        data-w-orderable-item-label="Item A"
    >
        Item A
        <button data-action="w-orderable#up">Up</button>
        <button data-action="w-orderable#down">Down</button>
    </li>
</ul>
```

**API Reference**: {controller}`w-orderable`

**Accessibility**:
- Includes helpers (`w-orderable#up`, `w-orderable#down`) for keyboard-accessible reordering.
- Dispatches success messages compatible with Wagtail's toaster notifications (`w-messages`).

**Limitations**:
- Requires an API endpoint that accepts POST requests with `position`.
- URL placeholder `999999` is replaced by the item ID.

(w-progress)=

## Progress `w-progress`

**Purpose**: Provides visual feedback for long-running actions (e.g. form submissions) by replacing the button label and disabling interaction for a set duration.

**Basic Usage**:

```html
<button
    type="submit"
    class="button button-longrunning"
    data-controller="w-progress"
    data-action="w-progress#activate"
    data-w-progress-active-value="Saving..."
>
    <!-- Icon (optional) -->
    <svg class="icon icon-spinner" ...></svg>
    <em data-w-progress-target="label">Save</em>
</button>
```

**API Reference**: {controller}`w-progress`

**Accessibility**:
- Disables the button to prevent double submission (if `w-progress#activate` is triggered).
- Updates the label text for screen readers.

**Limitations**:
- Automatically resets after the `duration` (default 30s) if the page hasn't reloaded.
- Respects HTML5 form validation (check validity before activating).

(w-action)=

## Action `w-action`

**Purpose**: Provides generic actions like clicking elements, dynamic form submissions, redirects, and text selection. useful for avoiding inline scripts.

**Basic Usage**:

```html
<!-- Dynamic POST request -->
<button
    type="button"
    data-controller="w-action"
    data-action="w-action#post"
    data-w-action-url-value="/admin/actions/enable/"
>
    Enable
</button>

<!-- Sync value with another element -->
<button
    type="button"
    data-controller="w-action"
    data-action="w-action#click"
>
    Triggers click on itself (useful with cross-controller actions)
</button>
```

**API Reference**: {controller}`w-action`

**Available Methods**:
- `post` / `sendBeacon`: POSTs to `urlValue`. `sendBeacon` is non-blocking.
- `click`: Clicks the element.
- `redirect`: Redirects to a URL (from params or value).
- `reset`: Resets input value.
- `select`: Selects text in input/textarea.
- `reload` / `forceReload`: Reloads page.
- `noop`: Does nothing (useful for stopping propagation).

**Accessibility**:
- Ensure custom triggers (like `div` with click handlers) have appropriate roles and keyboard support if not using native buttons.
