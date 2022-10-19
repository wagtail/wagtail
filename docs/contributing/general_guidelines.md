# General coding guidelines

## Language

British English is preferred for user-facing text; this text should also be marked for translation (using the `django.utils.translation.gettext` function and `{% trans %}` template tag, for example). However, identifiers within code should use American English if the British or international spelling would conflict with built-in language keywords; for example, CSS code should consistently use the spelling `color` to avoid inconsistencies like `background-color: $colour-red`.

### Latin phrases and abbreviations

Try to avoid Latin phrases (such as `ergo` or `de facto`) and abbreviations (such as `i.e.` or `e.g.`), and use common English phrases instead. Alternatively, find a simpler way to communicate the concept or idea to the reader. The exception is `etc.` which can be used when space is limited.

Examples:

| Don't use this | Use this instead     |
| -------------- | -------------------- |
| e.g.           | for example, such as |
| i.e.           | that is              |
| viz.           | namely               |
| ergo           | therefore            |

## File names

Where practical, try to adhere to the existing convention of file names within the folder where added.

Examples:

-   Django templates - `lower_snake_case.html`
-   Documentation - `lower_snake_case.md`
