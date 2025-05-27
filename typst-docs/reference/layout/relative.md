# relative

A length in relation to some known length.

This type is a combination of a [length](/docs/reference/layout/length/) with a [ratio](/docs/reference/layout/ratio/). It results from addition and subtraction of a length and a ratio. Wherever a relative length is expected, you can also use a bare length or ratio.

## Example

```typst
#rect(width: 100% - 50pt)

#(100% - 50pt).length \
#(100% - 50pt).ratio
```

A relative length has the following fields:

- `length`: Its length component.
- `ratio`: Its ratio component.
