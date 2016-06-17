# Icon

A simple component to render an icon. Abstracts away the actual icon implementation (font icons, SVG icons, CSS sprite).

## Usage

```javascript
import { Icon } from 'wagtail';

render(
    <Icon
        name="arrow-left"
        className="icon--active icon--warning"
        title="Move left"
    />
);
```

### Available props

- `name`: icon name
- `className`: additional CSS classes to add to the element
- `title`: accessible label intended for screen readers
