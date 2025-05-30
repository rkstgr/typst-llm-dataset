= numbering

Applies a numbering to a sequence of numbers.

A numbering defines how a sequence of numbers should be displayed as content. It is defined either through a pattern string or an arbitrary function.

A numbering pattern consists of counting symbols, for which the actual number is substituted, their prefixes, and one suffix. The prefixes and the suffix are repeated as-is.

== Example

```typst
#numbering("1.1)", 1, 2, 3) \
#numbering("1.a.i", 1, 2) \
#numbering("I – 1", 12, 2) \
#numbering(
  (..nums) => nums
    .pos()
    .map(str)
    .join(".") + ")",
  1, 2, 3,
)
```

== Numbering patterns and numbering functions

There are multiple instances where you can provide a numbering pattern or function in Typst. For example, when defining how to number #link("/docs/reference/model/heading/")[headings] or #link("/docs/reference/model/figure/")[figures]. Every time, the expected format is the same as the one described below for the #link("/docs/reference/model/numbering/#parameters-numbering")[numbering] parameter.

The following example illustrates that a numbering function is just a regular #link("/docs/reference/foundations/function/")[function] that accepts numbers and returns #link("/docs/reference/foundations/content/")[content].

```typst
#let unary(.., last) = "|" * last
#set heading(numbering: unary)
= First heading
= Second heading
= Third heading
```

== Parameters

```
numbering(
  str: str | function,
  ..: int
) -> int
```

=== `numbering`: str | function (Required, Positional)

Defines how the numbering works.

*Counting symbols* are `1`, `a`, `A`, `i`, `I`, `α`, `Α`, `一`, `壹`, `あ`, `い`, `ア`, `イ`, `א`, `가`, `ㄱ`, `*`, `١`, `۱`, `१`, `১`, `ক`, `①`, and `⓵`. They are replaced by the number in the sequence, preserving the original case.

The `*` character means that symbols should be used to count, in the order of `*`, `†`, `‡`, `§`, `¶`, `‖`. If there are more than six items, the number is represented using repeated symbols.

*Suffixes* are all characters after the last counting symbol. They are repeated as-is at the end of any rendered number.

*Prefixes* are all characters that are neither counting symbols nor suffixes. They are repeated as-is at in front of their rendered equivalent of their counting symbol.

This parameter can also be an arbitrary function that gets each number as an individual argument. When given a function, the `numbering` function just forwards the arguments to that function. While this is not particularly useful in itself, it means that you can just give arbitrary numberings to the `numbering` function without caring whether they are defined as a pattern or function.

=== `numbers`: int (Required, Positional, Variadic)

The numbers to apply the numbering to. Must be positive.

If `numbering` is a pattern and more numbers than counting symbols are given, the last counting symbol with its prefix is repeated.
