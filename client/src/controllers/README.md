# `src/controllers` folder

**Important:** This is a migration in progress, any large refactors or new code should adopt this approach.

-   Wagtail uses [Stimulus](https://stimulus.hotwired.dev/) as a way to attach interactive behavior to DOM elements.
-   This is a lightweight JavaScript framework that allows a JavaScript class to be attached to any DOM element that adheres to a specific usage of `data-` attributes on the element.
-   Each file within this folder should contain one Stimulus controller class, using a matching file name (for example `class MyAwesomeController, `MyAwesomeController.ts`, all TitleCase).
-   Controllers that are included in the `index.ts` default export will automatically be included in the core bundle and provided by default.
-   Stories need to be written as JavaScript for now - `MyController.stories.js` as the compiled JavaScript from StoryBook conflicts with Stimulus' usage of adding getters only on Controller instantiation.
