# Wagtail client-side components

This library aims to give developers the ability to subclass and configure Wagtail's UI components.

## Usage

```
npm install wagtail
```

```javascript
import { Explorer } from 'wagtail';

...

<Explorer onChoosePage={(page)=> { console.log(`You picked ${page}`); }} />

```

## Available components

TODO

- [ ] Explorer
- [ ] Modal
- [ ] DatePicker
- [ ] LinkChooser
- [ ] DropDown

## Building in development

Run `webpack` from the Wagtail project root.

```
webpack
```

## How to release

The front-end is bundled at the same time as the Wagtail project, via `setuptools`. You'll need to set the `__semver__` property to a npm-compliant version number in `wagtail.wagtailcore`.


