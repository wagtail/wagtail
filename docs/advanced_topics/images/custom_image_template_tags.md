# Creating custom image template tags

Wagtail provides a powerful built-in `{% image %}` template tag for rendering images.
However, in real-world projects, developers often need more control over how images
are rendered than the default tag allows.

This guide explains how to create custom image template tags using Wagtail’s image
APIs to implement opinionated rendering logic.

---

## When custom image tags are useful

Custom image template tags are helpful when you need to:

- Apply CSS classes based on image dimensions
- Enforce consistent design rules (for example, circular profile images)
- Add custom HTML attributes
- Implement dynamic resize rules
- Keep templates simple while centralizing image logic

---

## Overview of the approach

The general approach is:

1. Create a custom Django template tag
2. Generate image renditions using `image.get_rendition()`
3. Render HTML using `Rendition.img_tag()`
4. Apply any custom logic required for your project

---

## Example: rendering circular images

The following example demonstrates a custom template tag that renders square images
as circular by applying a CSS class.

### Creating the template tag

Create a `templatetags` directory in your app (if it does not already exist):
