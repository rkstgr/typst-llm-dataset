# arguments

Captured arguments to a function.

## Argument Sinks

Like built-in functions, custom functions can also take a variable number of arguments. You can specify an *argument sink* which collects all excess arguments as `..sink`. The resulting `sink` value is of the `arguments` type. It exposes methods to access the positional and named arguments.

```typst
#let format(title, ..authors) = {
  let by = authors
    .pos()
    .join(", ", last: " and ")

  [*#title* \ _Written by #by;_]
}

#format("ArtosFlow", "Jane", "Joe")
```

## Spreading

Inversely to an argument sink, you can *spread* arguments, arrays and dictionaries into a function call with the `..spread` operator:

```typst
#let array = (2, 3, 5)
#calc.min(..array)
#let dict = (fill: blue)
#text(..dict)[Hello]
```

## Constructor

Construct spreadable arguments in place.

This function behaves like `let args(..sink) = sink`.

```
arguments(
  ..: any
) -> arguments
```

```typst
#let args = arguments(stroke: red, inset: 1em, [Body])
#box(..args)
```

#### `arguments`: any (Required, Positional, Variadic)

The arguments to construct.

## Definitions

### `at`

Returns the positional argument at the specified index, or the named argument with the specified name.

If the key is an [integer](/docs/reference/foundations/int/), this is equivalent to first calling [pos](/docs/reference/foundations/arguments/#definitions-pos) and then [array.at](/docs/reference/foundations/array/#definitions-at). If it is a [string](/docs/reference/foundations/str/), this is equivalent to first calling [named](/docs/reference/foundations/arguments/#definitions-named) and then [dictionary.at](/docs/reference/foundations/dictionary/#definitions-at).

```
at(
  int: int | str,
  default: any
) -> str
```

#### `key`: int | str (Required, Positional)

The index or name of the argument to get.

#### `default`: any

A default value to return if the key is invalid.

### `pos`

Returns the captured positional arguments as an array.

```
pos(
  
) -> array
```

### `named`

Returns the captured named arguments as a dictionary.

```
named(
  
) -> dictionary
```
