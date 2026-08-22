from __future__ import annotations

import base64
import ctypes
import os


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _make_blob(data: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data)
    blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    return blob, buffer


def protect_text(value: str) -> str:
    if not value:
        return ""
    if os.name != "nt":
        raise RuntimeError("Encrypted secret storage currently requires Windows DPAPI.")
    crypt32 = ctypes.windll.crypt32
    input_blob, _buffer = _make_blob(value.encode("utf-8"))
    output_blob = _DataBlob()
    ok = crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob),
    )
    if not ok:
        raise ctypes.WinError()
    try:
        encrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
        return "dpapi:" + base64.b64encode(encrypted).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


def unprotect_text(value: str) -> str:
    if not value:
        return ""
    if not value.startswith("dpapi:"):
        raise ValueError("Unsupported secret format.")
    if os.name != "nt":
        raise RuntimeError("Encrypted secret storage currently requires Windows DPAPI.")
    raw = base64.b64decode(value.removeprefix("dpapi:"))
    crypt32 = ctypes.windll.crypt32
    input_blob, _buffer = _make_blob(raw)
    output_blob = _DataBlob()
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob),
    )
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData).decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)
