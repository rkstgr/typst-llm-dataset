# columns

Separates a region into multiple equally sized columns.

The `column` function lets you separate the interior of any container into multiple columns. It will currently not balance the height of the columns. Instead, the columns will take up the height of their container or the remaining height on the page. Support for balanced columns is planned for the future.

## Page-level columns

If you need to insert columns across your whole document, use the `page` function's [columns parameter](/docs/reference/layout/page/#parameters-columns) instead. This will create the columns directly at the page-level rather than wrapping all of your content in a layout container. As a result, things like [pagebreaks](/docs/reference/layout/pagebreak/), [footnotes](/docs/reference/model/footnote/), and [line numbers](/docs/reference/model/par/#definitions-line) will continue to work as expected. For more information, also read the [relevant part of the page setup guide](/docs/guides/page-setup-guide/#columns).

## Breaking out of columns

To temporarily break out of columns (e.g. for a paper's title), use parent-scoped floating placement:

```typst
#set page(columns: 2, height: 150pt)

#place(
  top + center,
  scope: "parent",
  float: true,
  text(1.4em, weight: "bold")[
    My document
  ],
)

#lorem(40)
```

## Parameters

```
columns(
  count: int,
  gutter: relative,
  content: content
) -> content
```

### `count`: int (Positional, Settable)

The number of columns.

Default: `2`

### `gutter`: relative (Settable)

The size of the gutter space between each column.

Default: `4% + 0pt`

### `body`: content (Required, Positional)

The content that should be layouted into the columns.
