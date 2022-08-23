# `src/controllers` folder

-   Each file within this folder should contain one Stimulus controller, with the filename `MyAwesomeController.ts` (UpperCamelCaseController.ts).
-   Controllers that are included in the core will automatically be registered with the prefix `w` (for example, `TabsController` will be registered with the identifier `w-tabs`).
-   However, if the controller has a static method `isIncludedInCore = false;` then it will not be automatically registered but it will be included in the JS bundle.
-   All Controller classes must inherit the `AbstractController` and not directly use Stimulus' controller (this will raise a linting error), this is so that base behaviour and overrides can easily be set up.
-   See `docs/contributing/ui_guidelines.md` for more information no how to build controllers and when to use Stimulus within Wagtail.
