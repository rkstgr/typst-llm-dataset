# mat

A matrix.

The elements of a row should be separated by commas, while the rows themselves should be separated by semicolons. The semicolon syntax merges preceding arguments separated by commas into an array. You can also use this special syntax of math function calls to define custom functions that take 2D data.

Content in cells can be aligned with the [align](/docs/reference/math/mat/#parameters-align) parameter, or content in cells that are in the same row can be aligned with the `&` symbol.

## Example

```typst
$ mat(
  1, 2, ..., 10;
  2, 2, ..., 10;
  dots.v, dots.v, dots.down, dots.v;
  10, 10, ..., 10;
) $
```

## Parameters

```
mat(
  delim: none | str | array | symbol,
  align: alignment,
  augment: none | int | dictionary,
  gap: relative,
  row-gap: relative,
  column-gap: relative,
  ..: array
) -> content
```

### `delim`: none | str | array | symbol (Settable)

The delimiter to use.

Can be a single character specifying the left delimiter, in which case the right delimiter is inferred. Otherwise, can be an array containing a left and a right delimiter.

Default: `("(", ")")`

**Example:**
```typst
#set math.mat(delim: "[")
$ mat(1, 2; 3, 4) $
```

### `align`: alignment (Settable)

The horizontal alignment that each cell should have.

Default: `center`

**Example:**
```typst
#set math.mat(align: right)
$ mat(-1, 1, 1; 1, -1, 1; 1, 1, -1) $
```

### `augment`: none | int | dictionary (Settable)

Draws augmentation lines in a matrix.

- `none`: No lines are drawn.
- A single number: A vertical augmentation line is drawn after the specified column number. Negative numbers start from the end.
- A dictionary: With a dictionary, multiple augmentation lines can be drawn both horizontally and vertically. Additionally, the style of the lines can be set. The dictionary can contain the following keys: hline: The offsets at which horizontal lines should be drawn. For example, an offset of 2 would result in a horizontal line being drawn after the second row of the matrix. Accepts either an integer for a single line, or an array of integers for multiple lines. Like for a single number, negative numbers start from the end. vline: The offsets at which vertical lines should be drawn. For example, an offset of 2 would result in a vertical line being drawn after the second column of the matrix. Accepts either an integer for a single line, or an array of integers for multiple lines. Like for a single number, negative numbers start from the end. stroke: How to stroke the line. If set to auto, takes on a thickness of 0.05em and square line caps.

Default: `none`

**Example:**
```typst
$ mat(1, 0, 1; 0, 1, 2; augment: #2) $
// Equivalent to:
$ mat(1, 0, 1; 0, 1, 2; augment: #(-1)) $
```

### `gap`: relative (Settable)

The gap between rows and columns.

This is a shorthand to set `row-gap` and `column-gap` to the same value.

Default: `0% + 0pt`

**Example:**
```typst
#set math.mat(gap: 1em)
$ mat(1, 2; 3, 4) $
```

### `row-gap`: relative (Settable)

The gap between rows.

Default: `0% + 0.2em`

**Example:**
```typst
#set math.mat(row-gap: 1em)
$ mat(1, 2; 3, 4) $
```

### `column-gap`: relative (Settable)

The gap between columns.

Default: `0% + 0.5em`

**Example:**
```typst
#set math.mat(column-gap: 1em)
$ mat(1, 2; 3, 4) $
```

### `rows`: array (Required, Positional, Variadic)

An array of arrays with the rows of the matrix.

**Example:**
```typst
#let data = ((1, 2, 3), (4, 5, 6))
#let matrix = math.mat(..data)
$ v := matrix $
```
