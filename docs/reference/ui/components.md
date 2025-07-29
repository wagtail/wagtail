(ui_components)=

# UI components

## Tooltip

A tooltip that can be attached to an HTML element to display additional information on hover or focus. It is powered by the [`TooltipController`](controller:TooltipController) (`w-tooltip`). To add a tooltip, attach the `w-tooltip` controller to an element and specify the properties using data attributes.

```html
<button
    type="button"
    data-controller="w-tooltip"
    data-w-tooltip-content-value="More detail here"
    data-w-tooltip-offset-value="[10, 15]"
    data-w-tooltip-placement-value="top"
>
  A button with a tooltip
</button>
```

If you need the tooltip to display rich content, you can use an HTML element as the content target with a `data-w-tooltip-target="content"` attribute inside the `w-tooltip` element:

```html
<button
    type="button"
    data-controller="w-tooltip"
    data-w-tooltip-offset-value="[10, 15]"
    data-w-tooltip-placement-value="top"
>
  <template data-w-tooltip-target="content">
    More <strong>detail</strong> here
  </template>
  A button with a tooltip
</button>
```

Available value attributes for `w-tooltip`:

- `data-w-tooltip-content-value`: The content of the tooltip. Optional if a content target is used instead.
- `data-w-tooltip-offset-value` (optional): The offset of the tooltip from the element, specified as an array of two numbers (`[skidding, distance]`). Defaults to `[0, 10]`.
- `data-w-tooltip-placement-value` (optional): The placement of the tooltip relative to the element. Possible values are `top`, `top-start`, `top-end`, `right`, `right-start`, `right-end`, `bottom`, `bottom-start`, `bottom-end`, `left`, `left-start`, `left-end`. Defaults to `bottom`.
