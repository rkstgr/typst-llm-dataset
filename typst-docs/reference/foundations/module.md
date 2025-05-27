# module

An module of definitions.

A module

- be built-in
- stem from a [file import](/docs/reference/scripting/#modules)
- stem from a [package import](/docs/reference/scripting/#packages) (and thus indirectly its entrypoint file)
- result from a call to the [plugin](/docs/reference/foundations/plugin/) function

You can access definitions from the module using [field access notation](/docs/reference/scripting/#fields) and interact with it using the [import and include syntaxes](/docs/reference/scripting/#modules). Alternatively, it is possible to convert a module to a dictionary, and therefore access its contents dynamically, using the [dictionary constructor](/docs/reference/foundations/dictionary/#constructor).

## Example

```typst
#import "utils.typ"
#utils.add(2, 5)

#import utils: sub
#sub(1, 4)
```
