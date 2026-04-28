# raylib-kern

`raylib-kern` provides Kern bindings for [raylib](https://www.raylib.com/).
The Craft package name is `raylib`, so consumers import it with:

```kern
use raylib;
```

This repository is intentionally a normal third-party Kern package rather than
a generated artifact checked into another workspace. The public shape is:

- `raylib.raw`: direct C ABI declarations using raylib's C names.
- `raylib`: Kern-style type aliases, scalar constants, color constructors, and small helpers.

## Requirements

Install raylib development headers and libraries before building examples or
applications that link this package.

On many Linux distributions the dynamic package is enough:

```sh
pkg-config --modversion raylib
```

If raylib is installed in a custom prefix, expose it through the system linker
search path before invoking Craft. The build script links `raylib` and common
platform libraries for Linux, macOS, and Windows.

## Quick Start

```toml
[dependencies]
raylib = { git = "https://example.invalid/raylib-kern.git" }
```

Local development can use a path dependency:

```toml
[dependencies]
raylib = { path = "../raylib-kern" }
```

Run the included example after raylib is installed:

```sh
craft build --examples
```

## Strings

raylib's C API expects zero-terminated `const char *` strings. Kern string
literals are slices, so the binding does not silently pretend every `[]u8` is a
C string. Helpers such as `init_window` and `draw_text` accept `[]u8` values
that must already contain a trailing zero byte:

```kern
const TITLE = [6]u8.{ b'H', b'e', b'l', b'l', b'o', 0 };
raylib.init_window(800, 450, TITLE.[0 .. 6]);
```

When that is not the shape you want, call `raylib.raw.*` directly or allocate a
temporary C string with `base.abi.cstr`.

## Colors

raylib's named colors are exposed as functions such as `raylib.raywhite()` and
`raylib.darkgray()`. This avoids exporting aggregate constants until Kern's
cross-package constant linkage has a stable story.

## Scope

The first binding pass targets raylib 5.x's stable C ABI and covers core,
shapes, textures, text, models, and audio. Variadic C helpers are deliberately
not wrapped as Kern varargs until the language has a clear FFI story for them.

## License

MIT. raylib itself is distributed separately under its own license.
