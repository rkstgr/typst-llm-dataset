= outline

A table of contents, figures, or other elements.

This function generates a list of all occurrences of an element in the document, up to a given #link("/docs/reference/model/outline/#parameters-depth")[depth]. The element's numbering and page number will be displayed in the outline alongside its title or caption.

== Example

```typst
#set heading(numbering: "1.")
#outline()

= Introduction
#lorem(5)

= Methods
== Setup
#lorem(10)
```

== Alternative outlines

In its default configuration, this function generates a table of contents. By setting the `target` parameter, the outline can be used to generate a list of other kinds of elements than headings.

In the example below, we list all figures containing images by setting `target` to `figure.where(kind: image)`. Just the same, we could have set it to `figure.where(kind: table)` to generate a list of tables.

We could also set it to just `figure`, without using a #link("/docs/reference/foundations/function/#definitions-where")[where] selector, but then the list would contain _all_ figures, be it ones containing images, tables, or other material.

```typst
#outline(
  title: [List of Figures],
  target: figure.where(kind: image),
)

#figure(
  image("tiger.jpg"),
  caption: [A nice figure!],
)
```

== Styling the outline

At the most basic level, you can style the outline by setting properties on it and its entries. This way, you can customize the outline's #link("/docs/reference/model/outline/#parameters-title")[title], how outline entries are #link("/docs/reference/model/outline/#parameters-indent")[indented], and how the space between an entry's text and its page number should be #link("/docs/reference/model/outline/#definitions-entry-fill")[filled].

Richer customization is possible through configuration of the outline's #link("/docs/reference/model/outline/#definitions-entry")[entries]. The outline generates one entry for each outlined element.

Outline entries are #link("/docs/reference/layout/block/")[blocks], so you can adjust the spacing between them with normal block-spacing rules:

```typst
#show outline.entry.where(
  level: 1
): set block(above: 1.2em)

#outline()

= About ACME Corp.
== History
=== Origins
= Products
== ACME Tools
```

For full control, you can also write a transformational show rule on `outline.entry`. However, the logic for properly formatting and indenting outline entries is quite complex and the outline entry itself only contains two fields: The level and the outlined element.

For this reason, various helper functions are provided. You can mix and match these to compose an entry from just the parts you like.

The default show rule for an outline entry looks like this1:

- The indented function takes an optional prefix and inner content and automatically applies the proper indentation to it, such that different entries align nicely and long headings wrap properly.
- The prefix function formats the element's numbering (if any). It also appends a supplement for certain elements.
- The inner function combines the element's body, the filler, and the page number.

You can use these individual functions to format the outline entry in different ways. Let's say, you'd like to fully remove the filler and page numbers. To achieve this, you could write a show rule like this:

```typst
#show outline.entry: it => link(
  it.element.location(),
  // Keep just the body, dropping
  // the fill and the page.
  it.indented(it.prefix(), it.body()),
)

#outline()

= About ACME Corp.
== History
```

== Parameters

```
outline(
  title: none | auto | content,
  target: label | selector | location | function,
  depth: none | int,
  indent: auto | relative | function
) -> content
```

=== `title`: none | auto | content (Settable)

The title of the outline.

- When set to `auto`, an appropriate title for the #link("/docs/reference/text/text/#parameters-lang")[text language] will be used.
- When set to `none`, the outline will not have a title.
- A custom title can be set by passing content.

The outline's heading will not be numbered by default, but you can force it to be with a show-set rule: `show outline: set heading(numbering: "1.")`

Default: `auto`

=== `target`: label | selector | location | function (Settable)

The type of element to include in the outline.

To list figures containing a specific kind of element, like an image or a table, you can specify the desired kind in a #link("/docs/reference/foundations/function/#definitions-where")[where] selector. See the section on #link("/docs/reference/model/outline/#alternative-outlines")[alternative outlines] for more details.

Default: `heading`

*Example:*
```typst
#outline(
  title: [List of Tables],
  target: figure.where(kind: table),
)

#figure(
  table(
    columns: 4,
    [t], [1], [2], [3],
    [y], [0.3], [0.7], [0.5],
  ),
  caption: [Experiment results],
)
```

=== `depth`: none | int (Settable)

The maximum level up to which elements are included in the outline. When this argument is `none`, all elements are included.

Default: `none`

*Example:*
```typst
#set heading(numbering: "1.")
#outline(depth: 2)

= Yes
Top-level section.

== Still
Subsection.

=== Nope
Not included.
```

=== `indent`: auto | relative | function (Settable)

How to indent the outline's entries.

- auto: Indents the numbering/prefix of a nested entry with the title of its parent entry. If the entries are not numbered (e.g., via heading numbering), this instead simply inserts a fixed amount of 1.2em indent per level.
- Relative length: Indents the entry by the specified length per nesting level. Specifying 2em, for instance, would indent top-level headings by 0em (not nested), second level headings by 2em (nested once), third-level headings by 4em (nested twice) and so on.
- Function: You can further customize this setting with a function. That function receives the nesting level as a parameter (starting at 0 for top-level headings/elements) and should return a (relative) length. For example, n => n * 2em would be equivalent to just specifying 2em.

Default: `auto`

*Example:*
```typst
#set heading(numbering: "1.a.")

#outline(
  title: [Contents (Automatic)],
  indent: auto,
)

#outline(
  title: [Contents (Length)],
  indent: 2em,
)

= About ACME Corp.
== History
=== Origins
#lorem(10)

== Products
#lorem(10)
```

== Definitions

=== `entry`

Represents an entry line in an outline.

With show-set and show rules on outline entries, you can richly customize the outline's appearance. See the #link("/docs/reference/model/outline/#styling-the-outline")[section on styling the outline] for details.

```
entry(
  int: int,
  content: content,
  fill: none | content
) -> content
```

==== `level`: int (Required, Positional)

The nesting level of this outline entry. Starts at `1` for top-level entries.

==== `element`: content (Required, Positional)

The element this entry refers to. Its location will be available through the #link("/docs/reference/foundations/content/#definitions-location")[location] method on the content and can be #link("/docs/reference/model/link/")[linked] to.

==== `fill`: none | content (Settable)

Content to fill the space between the title and the page number. Can be set to `none` to disable filling.

The `fill` will be placed into a fractionally sized box that spans the space between the entry's body and the page number. When using show rules to override outline entries, it is thus recommended to wrap the fill in a #link("/docs/reference/layout/box/")[box] with fractional width, i.e. `box(width: 1fr, it.fill`.

When using #link("/docs/reference/layout/repeat/")[repeat], the #link("/docs/reference/layout/repeat/#parameters-gap")[gap] property can be useful to tweak the visual weight of the fill.

Default: `repeat(body: [.], gap: 0.15em)`

*Example:*
```typst
#set outline.entry(fill: line(length: 100%))
#outline()

= A New Beginning
```

== Definitions of entry

=== `indented`

A helper function for producing an indented entry layout: Lays out a prefix and the rest of the entry in an indent-aware way.

If the parent outline's #link("/docs/reference/model/outline/#parameters-indent")[indent] is `auto`, the inner content of all entries at level `N` is aligned with the prefix of all entries at level `N + 1`, leaving at least `gap` space between the prefix and inner parts. Furthermore, the `inner` contents of all entries at the same level are aligned.

If the outline's indent is a fixed value or a function, the prefixes are indented, but the inner contents are simply inset from the prefix by the specified `gap`, rather than aligning outline-wide.

```
indented(
  none: none | content,
  content: content,
  gap: length
) -> content
```

==== `prefix`: none | content (Required, Positional)

The `prefix` is aligned with the `inner` content of entries that have level one less.

In the default show rule, this is just `it.prefix()`, but it can be freely customized.

==== `inner`: content (Required, Positional)

The formatted inner content of the entry.

In the default show rule, this is just `it.inner()`, but it can be freely customized.

==== `gap`: length

The gap between the prefix and the inner content.

Default: `0.5em`

=== `prefix`

Formats the element's numbering (if any).

This also appends the element's supplement in case of figures or equations. For instance, it would output `1.1` for a heading, but `Figure 1` for a figure, as is usual for outlines.

```
prefix(
  
) -> content
```

=== `inner`

Creates the default inner content of the entry.

This includes the body, the fill, and page number.

```
inner(
  
) -> content
```

=== `body`

The content which is displayed in place of the referred element at its entry in the outline. For a heading, this is its #link("/docs/reference/model/heading/#parameters-body")[body]; for a figure a caption and for equations, it is empty.

```
body(
  
) -> content
```

=== `page`

The page number of this entry's element, formatted with the numbering set for the referenced page.

```
page(
  
) -> content
```
