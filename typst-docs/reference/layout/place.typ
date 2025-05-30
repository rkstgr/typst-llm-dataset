= place

Places content relatively to its parent container.

Placed content can be either overlaid (the default) or floating. Overlaid content is aligned with the parent container according to the given #link("/docs/reference/layout/place/#parameters-alignment")[alignment], and shown over any other content added so far in the container. Floating content is placed at the top or bottom of the container, displacing other content down or up respectively. In both cases, the content position can be adjusted with #link("/docs/reference/layout/place/#parameters-dx")[dx] and #link("/docs/reference/layout/place/#parameters-dy")[dy] offsets without affecting the layout.

The parent can be any container such as a #link("/docs/reference/layout/block/")[block], #link("/docs/reference/layout/box/")[box], #link("/docs/reference/visualize/rect/")[rect], etc. A top level `place` call will place content directly in the text area of the current page. This can be used for absolute positioning on the page: with a `top + left` #link("/docs/reference/layout/place/#parameters-alignment")[alignment], the offsets `dx` and `dy` will set the position of the element's top left corner relatively to the top left corner of the text area. For absolute positioning on the full page including margins, you can use `place` in #link("/docs/reference/layout/page/#parameters-foreground")[page.foreground] or #link("/docs/reference/layout/page/#parameters-background")[page.background].

== Examples

```typst
#set page(height: 120pt)
Hello, world!

#rect(
  width: 100%,
  height: 2cm,
  place(horizon + right, square()),
)

#place(
  top + left,
  dx: -5pt,
  square(size: 5pt, fill: red),
)
```

== Effect on the position of other elements

Overlaid elements don't take space in the flow of content, but a `place` call inserts an invisible block-level element in the flow. This can affect the layout by breaking the current paragraph. To avoid this, you can wrap the `place` call in a #link("/docs/reference/layout/box/")[box] when the call is made in the middle of a paragraph. The alignment and offsets will then be relative to this zero-size box. To make sure it doesn't interfere with spacing, the box should be attached to a word using a word joiner.

For example, the following defines a function for attaching an annotation to the following word:

```typst
#let annotate(..args) = {
  box(place(..args))
  sym.wj
  h(0pt, weak: true)
}

A placed #annotate(square(), dy: 2pt)
square in my text.
```

The zero-width weak spacing serves to discard spaces between the function call and the next word.

== Parameters

```
place(
  alignment: auto | alignment,
  scope: str,
  float: bool,
  clearance: length,
  dx: relative,
  dy: relative,
  content: content
) -> content
```

=== `alignment`: auto | alignment (Positional, Settable)

Relative to which position in the parent container to place the content.

- If `float` is `false`, then this can be any alignment other than `auto`.
- If `float` is `true`, then this must be `auto`, `top`, or `bottom`.

When `float` is `false` and no vertical alignment is specified, the content is placed at the current position on the vertical axis.

Default: `start`

=== `scope`: str (Settable)

Relative to which containing scope something is placed.

The parent scope is primarily used with figures and, for this reason, the figure function has a mirrored #link("/docs/reference/model/figure/#parameters-scope")[scope parameter]. Nonetheless, it can also be more generally useful to break out of the columns. A typical example would be to #link("/docs/guides/page-setup-guide/#columns")[create a single-column title section] in a two-column document.

Note that parent-scoped placement is currently only supported if `float` is `true`. This may change in the future.

Default: `"column"`

*Example:*
```typst
#set page(height: 150pt, columns: 2)
#place(
  top + center,
  scope: "parent",
  float: true,
  rect(width: 80%, fill: aqua),
)

#lorem(25)
```

=== `float`: bool (Settable)

Whether the placed element has floating layout.

Floating elements are positioned at the top or bottom of the parent container, displacing in-flow content. They are always placed in the in-flow order relative to each other, as well as before any content following a later #link("/docs/reference/layout/place/#definitions-flush")[place.flush] element.

Default: `false`

*Example:*
```typst
#set page(height: 150pt)
#let note(where, body) = place(
  center + where,
  float: true,
  clearance: 6pt,
  rect(body),
)

#lorem(10)
#note(bottom)[Bottom 1]
#note(bottom)[Bottom 2]
#lorem(40)
#note(top)[Top]
#lorem(10)
```

=== `clearance`: length (Settable)

The spacing between the placed element and other elements in a floating layout.

Has no effect if `float` is `false`.

Default: `1.5em`

=== `dx`: relative (Settable)

The horizontal displacement of the placed content.

Default: `0% + 0pt`

*Example:*
```typst
#set page(height: 100pt)
#for i in range(16) {
  let amount = i * 4pt
  place(center, dx: amount - 32pt, dy: amount)[A]
}
```

=== `dy`: relative (Settable)

The vertical displacement of the placed content.

This does not affect the layout of in-flow content. In other words, the placed content is treated as if it were wrapped in a #link("/docs/reference/layout/move/")[move] element.

Default: `0% + 0pt`

=== `body`: content (Required, Positional)

The content to place.

== Definitions

=== `flush`

Asks the layout algorithm to place pending floating elements before continuing with the content.

This is useful for preventing floating figures from spilling into the next section.

```
flush(
  
) -> content
```

```typst
#lorem(15)

#figure(
  rect(width: 100%, height: 50pt),
  placement: auto,
  caption: [A rectangle],
)

#place.flush()

This text appears after the figure.
```
