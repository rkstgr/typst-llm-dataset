# colbreak

Forces a column break.

The function will behave like a [page break](/docs/reference/layout/pagebreak/) when used in a single column layout or the last column on a page. Otherwise, content after the column break will be placed in the next column.

## Example

```typst
#set page(columns: 2)
Preliminary findings from our
ongoing research project have
revealed a hitherto unknown
phenomenon of extraordinary
significance.

#colbreak()
Through rigorous experimentation
and analysis, we have discovered
a hitherto uncharacterized process
that defies our current
understanding of the fundamental
laws of nature.
```

## Parameters

```
colbreak(
  weak: bool
) -> content
```

### `weak`: bool (Settable)

If `true`, the column break is skipped if the current column is already empty.

Default: `false`
