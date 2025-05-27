# locate

Determines the location of an element in the document.

Takes a selector that must match exactly one element and returns that element's [location](/docs/reference/introspection/location/). This location can, in particular, be used to retrieve the physical [page](/docs/reference/introspection/location/#definitions-page) number and [position](/docs/reference/introspection/location/#definitions-position) (page, x, y) for that element.

## Examples

Locating a specific element:

```typst
#context [
  Introduction is at: \
  #locate(<intro>).position()
]

= Introduction <intro>
```

## Parameters

```
locate(
  label: label | selector | location | function
) -> location
```

### `selector`: label | selector | location | function (Required, Positional)

A selector that should match exactly one element. This element will be located.

Especially useful in combination with

- [here](/docs/reference/introspection/here/) to locate the current context,
- a [location](/docs/reference/introspection/location/) retrieved from some queried element via the [location()](/docs/reference/foundations/content/#definitions-location) method on content.
