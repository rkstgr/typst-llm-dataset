= repeat

Repeats content to the available space.

This can be useful when implementing a custom index, reference, or outline.

Space may be inserted between the instances of the body parameter, so be sure to adjust the #link("/docs/reference/layout/repeat/#parameters-justify")[justify] parameter accordingly.

Errors if there are no bounds on the available space, as it would create infinite content.

== Example

```typst
Sign on the dotted line:
#box(width: 1fr, repeat[.])

#set text(10pt)
#v(8pt, weak: true)
#align(right)[
  Berlin, the 22nd of December, 2022
]
```

== Parameters

```
repeat(
  content: content,
  gap: length,
  justify: bool
) -> content
```

=== `body`: content (Required, Positional)

The content to repeat.

=== `gap`: length (Settable)

The gap between each instance of the body.

Default: `0pt`

=== `justify`: bool (Settable)

Whether to increase the gap between instances to completely fill the available space.

Default: `true`
