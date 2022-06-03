# Wagtail client-side components

> This library aims to give developers the ability to subclass and configure Wagtail's UI components.

## Usage

```sh
npm install wagtail
```

```javascript
import { Explorer } from 'wagtail';
// [...]
<Explorer />;
```

## Development

```sh
# From the project root, start the webpack + styles compilation.
npm run start
```

You will also need:

-   [React DevTools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi?hl=en) – React developer tools integrated into Chrome.
-   [Redux DevTools](https://chrome.google.com/webstore/detail/redux-devtools/lmhkpmbekcpmknklioeibfkpmmfibljd) – Redux developer tools integrated into Chrome.

## Releases

The front-end is bundled at the same time as the Wagtail project. This package also aims to be available separately on npm as [`wagtail`](https://www.npmjs.com/package/wagtail).
