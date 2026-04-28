# raylib-kern

`raylib-kern` provides Kern bindings for [raylib](https://www.raylib.com/).
The Craft package name is `raylib`, so consumers import it with:

```kern
use raylib;
```

This repository is intentionally a normal third-party Kern package rather than
a generated artifact checked into another workspace. It pins raylib as a Craft
resource and builds the C sources through Craft instead of requiring a system
`libraylib`.

The public shape is:

- `raylib.raw`: direct C ABI declarations using raylib's C names.
- `raylib`: Kern-style type aliases, constants, color constructors, and small helpers.

## Requirements

Craft fetches raylib from Git and compiles the required C modules from the
resource tree. Platform system libraries are still linked by the build script.
On Linux that means OpenGL and X11 development libraries must be present for
examples or applications to link.

On Fedora:

```sh
sudo dnf install mesa-libGL-devel libX11-devel libXrandr-devel libXinerama-devel libXi-devel libXcursor-devel
```

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

Run the included example after platform development libraries are installed:

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

raylib's named colors are exposed as `pub const` values such as
`raylib.RAYWHITE` and `raylib.DARKGRAY`. They rely on Kern's `const`
compile-time semantics and must not lower to linkable global storage.

## Binding Generation

raylib changes its API regularly. The long-term source of truth for this package
is raylib's parser output, not a hand-maintained copy of `raylib.h`. Craft builds
and runs the Kern host tool in `tools/raylib-bindgen` against
`tools/rlparser/output/raylib_api.txt` from the pinned raylib resource.

## Scope

The first binding pass targets raylib 6.0's stable C ABI and covers core,
shapes, textures, text, models, and audio. Variadic C helpers are deliberately
not wrapped as Kern varargs until the language has a clear FFI story for them.

## License

MIT. raylib itself is distributed separately under its own license.
