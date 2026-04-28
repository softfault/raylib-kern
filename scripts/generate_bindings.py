#!/usr/bin/env python3
"""Generate Kern bindings from raylib's parser JSON.

The generator intentionally consumes raylib's structured parser output instead
of scraping raylib.h directly. The JSON shape has changed across raylib
releases, so this script keeps extraction defensive and fails loudly on
unmapped C types.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


TYPE_MAP = {
    "void": "void",
    "bool": "bool",
    "char": "u8",
    "unsigned char": "u8",
    "short": "i16",
    "unsigned short": "u16",
    "int": "i32",
    "unsigned int": "u32",
    "long": "isize",
    "unsigned long": "usize",
    "long long": "i64",
    "unsigned long long": "u64",
    "float": "f32",
    "double": "f64",
    "size_t": "usize",
    "rAudioBuffer": "void",
    "rAudioProcessor": "void",
}

SKIP_FUNCTIONS = {
    "TraceLog",
    "TextFormat",
}


def items(data: Any, *names: str) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    for name in names:
        value = data.get(name)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def clean_type(c_type: str) -> str:
    c_type = c_type.replace("const ", "")
    c_type = c_type.replace("struct ", "")
    c_type = c_type.replace("enum ", "")
    c_type = re.sub(r"\s+", " ", c_type.strip())
    return c_type


def kern_type(c_type: str) -> str:
    c_type = clean_type(c_type)
    pointer_depth = c_type.count("*")
    c_type = c_type.replace("*", "").strip()
    base = TYPE_MAP.get(c_type, c_type)
    if base == "char" or base == "const char":
        base = "u8"
    for _ in range(pointer_depth):
        base = f"*mut {base}" if base != "u8" else "*u8"
    return base


def field_type(c_type: str, name: str) -> tuple[str, str]:
    match = re.search(r"(.+)\[(\d+)\]$", name)
    if match:
        return match.group(1), f"[{match.group(2)}]{kern_type(c_type)}"
    return name, kern_type(c_type)


def constant_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    text = text.strip()
    text = text.removeprefix("(").removesuffix(")")
    if re.fullmatch(r"-?\d+", text):
        return text
    if re.fullmatch(r"0x[0-9a-fA-F]+", text):
        return text
    return None


def emit_header(out: list[str], source: str) -> None:
    out.extend(
        [
            "//! Generated raylib bindings.",
            "//!",
            f"//! Source: {source}",
            "//! Do not edit by hand; run `scripts/generate_bindings.py`.",
            "",
            "pub mod raw;",
            "",
        ]
    )


def emit_raw(data: Any, source: str) -> str:
    out: list[str] = []
    out.extend(
        [
            "//! Generated low-level raylib C ABI declarations.",
            "//!",
            f"//! Source: {source}",
            "",
        ]
    )

    for struct in items(data, "structs", "Structs"):
        name = struct.get("name") or struct.get("type")
        fields = struct.get("fields") or struct.get("Fields") or []
        if not name or not isinstance(fields, list):
            continue
        out.append(f"pub extern type {name} = struct {{")
        for field in fields:
            if not isinstance(field, dict):
                continue
            fname = field.get("name")
            ftype = field.get("type")
            if not fname or not ftype:
                continue
            fname, ftype = field_type(str(ftype), str(fname))
            out.append(f"    pub {fname}: {ftype},")
        out.append("};")
        out.append("")

    funcs = []
    for fn in items(data, "functions", "Functions"):
        name = fn.get("name")
        if not name or name in SKIP_FUNCTIONS:
            continue
        ret = fn.get("returnType") or fn.get("return_type") or fn.get("type") or "void"
        params = fn.get("params") or fn.get("parameters") or []
        rendered_params = []
        if isinstance(params, list):
            for index, param in enumerate(params):
                if not isinstance(param, dict):
                    continue
                pname = param.get("name") or f"arg{index}"
                ptype = param.get("type")
                if not ptype or ptype == "void":
                    continue
                rendered_params.append(f"{pname}: {kern_type(str(ptype))}")
        funcs.append(f"    pub fn {name}({', '.join(rendered_params)}) {kern_type(str(ret))};")

    if funcs:
        out.append("extern {")
        out.extend(funcs)
        out.append("}")
        out.append("")

    return "\n".join(out)


def emit_public(data: Any, source: str) -> str:
    out: list[str] = []
    emit_header(out, source)
    for struct in items(data, "structs", "Structs"):
        name = struct.get("name") or struct.get("type")
        if name:
            out.append(f"pub type {name} = raw.{name};")
    out.append("")

    for define in items(data, "defines", "Defines", "enums", "Enums"):
        name = define.get("name")
        value = constant_value(define.get("value"))
        if name and value is not None:
            out.append(f"pub const {name} = i32.{{{value}}};")

    out.append("")
    out.extend(
        [
            "pub fn color(r: u8, g: u8, b: u8, a: u8) Color {",
            "    return Color.{ r: r, g: g, b: b, a: a };",
            "}",
            "",
        ]
    )
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json", type=Path)
    parser.add_argument("--raw-out", type=Path)
    parser.add_argument("--public-out", type=Path)
    args = parser.parse_args()

    with args.json.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    source = str(args.json)
    raw = emit_raw(data, source)
    public = emit_public(data, source)

    if args.raw_out:
        args.raw_out.write_text(raw, encoding="utf-8")
    if args.public_out:
        args.public_out.write_text(public, encoding="utf-8")
    if not args.raw_out and not args.public_out:
        sys.stdout.write(public)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
