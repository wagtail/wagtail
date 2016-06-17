# PublishStatus

Displays the publication status of a page in a pill.

## Usage

```javascript
import { PublishStatus } from 'wagtail';

render(
    <PublishStatus
        status={status}
    />
);
```

### Available props

- `status`: status object coming from the admin API. If no status is given, component renders to null.
