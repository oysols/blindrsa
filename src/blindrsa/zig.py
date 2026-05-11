import array
import ctypes
import enum
import struct
from typing import Any


class ZigTypeFormat(enum.StrEnum):
    f64 = "d"
    f32 = "l"
    i64 = "q"
    u8 = "B"
    i8 = "b"
    bool = "?"
    usize = "N"


pointer = ctypes.c_void_p
f64 = ctypes.c_double
f32 = ctypes.c_float
i64 = ctypes.c_int64
u8 = ctypes.c_uint8
i8 = ctypes.c_int8
bool = ctypes.c_bool
usize = ctypes.c_size_t
c_char_p = ctypes.c_char_p


def pointer_to_bytes(obj: bytes) -> ctypes.c_void_p:
    return ctypes.c_void_p.from_param(obj)  # type: ignore[return-value]


def pointer_to_bytearray(arr: bytearray) -> ctypes.c_void_p:
    return ctypes.c_void_p(ctypes.addressof(ctypes.c_char.from_buffer(arr)))


def pointer_to_memoryview(mv: memoryview) -> ctypes.c_void_p:
    return ctypes.c_void_p.from_buffer(mv)


def pointer_to_array(arr: array.ArrayType[Any]) -> ctypes.c_void_p:
    return ctypes.c_void_p(ctypes.addressof(ctypes.c_char.from_buffer(arr)))


def create_bytearray_buffer(length: int, type_format: ZigTypeFormat) -> bytearray:
    return bytearray(length * struct.calcsize(type_format))


def pointer_to_value(obj: f64 | f32 | i64 | u8 | i8 | bool | usize) -> ctypes.c_void_p:
    return ctypes.byref(obj)  # type: ignore[return-value]


class ZigError(Exception):
    """Zig @errorName(err) propagated to python
    zig:
        fn myfunc() ?[*:0]const u8 {
            maybe_something() catch |err| return @errorName(err)
        }
    python:
        _lib.myfunc.restype = ctypes.c_char_p
        if err := _lib.myfunc():
            raise zig.ZigError(err)
    """

    def __init__(self, msg: bytes) -> None:
        super().__init__(msg.decode())


class ZigExports:
    def __init__(self, dll: ctypes.CDLL, exported_string_name: str, strip: list[str]) -> None:
        """Read explicitly created c_string containing lib function exports"""
        self.exports: list[str] = []
        for export in (ctypes.c_char_p.in_dll(dll, exported_string_name).value or b"").decode().splitlines():
            for strip_str in strip:
                export = export.replace(strip_str, "")
            self.exports.append(export)

    def assert_fn(self, function: str) -> None:
        """Assert the fn signature contract between python and zig"""
        if function not in self.exports:
            fname, *_ = function.split("(")
            for exported_fn in self.exports:
                match_fname, *_ = exported_fn.split("(")
                if fname == match_fname:
                    raise Exception(
                        "Function arguments does not match exports\n"
                        + f"  {function}\n"
                        + f"Expected:\n  {exported_fn}"
                    )
            signatures_string = "\n  ".join([sig for sig in self.exports])
            raise Exception(
                "Function not in lib exports.\n" + f"  {function}\n" + f"Expected one of:\n  {signatures_string}"
            )
