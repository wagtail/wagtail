(admin_ui_reference)=

# Admin UI reference

Wagtail includes a wide range of user interface (UI) components that are used to build the features within the CMS. These components are built using a combination of Django templates, [template components](template_components), custom Python classes, and JavaScript. They start out as internal components, but they are designed with extensibility and reusability in mind.

We acknowledge the usefulness of reusable components and their documentation for developers building custom features or third-party packages. While we strive to maintain a stable API for these components, we also need them to evolve rapidly to allow for continuous improvements to Wagtail's user interface.

```{include} ../../../client/README.md
:start-after: <!-- STABILITY:START -->
:end-before: <!-- STABILITY:END -->
```

For more details, see our [](deprecation_policy).

```{toctree}
---
maxdepth: 2
titlesonly:
---

components
client
```
