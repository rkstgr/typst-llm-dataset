= stretch

Stretches a glyph.

This function can also be used to automatically stretch the base of an attachment, so that it fits the top and bottom attachments.

Note that only some glyphs can be stretched, and which ones can depend on the math font being used. However, most math fonts are the same in this regard.

```typst
$ H stretch(=)^"define" U + p V $
$ f : X stretch(->>, size: #150%)_"surjective" Y $
$ x stretch(harpoons.ltrb, size: #3em) y
    stretch(\[, size: #150%) z $
```

== Parameters

```
stretch(
  content: content,
  size: relative
) -> content
```

=== `body`: content (Required, Positional)

The glyph to stretch.

=== `size`: relative (Settable)

The size to stretch to, relative to the maximum size of the glyph and its attachments.

Default: `100% + 0pt`
