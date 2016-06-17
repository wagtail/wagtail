# PublicationStatus

Displays the publication status of a page in a pill.

## Usage

```javascript
import { PublicationStatus } from 'wagtail';

render(
    <PublicationStatus
        status={status}
    />
);
```

### Available props

- `status`: status object coming from the admin API. If no status is given, component renders to null.
