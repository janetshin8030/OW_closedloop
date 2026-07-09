"""Minimal XDF file writer.

pyxdf (the library used elsewhere in this repo to read .xdf files) only
supports reading, not writing. This implements just enough of the XDF 1.0
binary format -- https://github.com/sccn/xdf/wiki/Specifications -- to build
synthetic test fixtures: FileHeader, StreamHeader, Samples (with an explicit
per-sample timestamp), and StreamFooter chunks. Clock-offset chunks are
intentionally omitted; pyxdf.load_xdf skips clock synchronization for any
stream with no such chunks, so timestamps are taken at face value.
"""
from __future__ import annotations

import struct
from io import BytesIO

import numpy as np

_NUMERIC_DTYPES = {"float32": "<f4", "double64": "<f8"}


def _varlen_int(n):
    if n < 2**8:
        return bytes([1, n])
    elif n < 2**32:
        return bytes([4]) + struct.pack("<I", n)
    else:
        return bytes([8]) + struct.pack("<Q", n)


def _chunk(tag, content):
    return _varlen_int(2 + len(content)) + struct.pack("<H", tag) + content


def _stream_header_xml(name, stype, channel_count, channel_format, nominal_srate, source_id):
    return (
        '<?xml version="1.0"?><info>'
        f"<name>{name}</name><type>{stype}</type>"
        f"<channel_count>{channel_count}</channel_count>"
        f"<channel_format>{channel_format}</channel_format>"
        f"<source_id>{source_id}</source_id>"
        f"<nominal_srate>{nominal_srate}</nominal_srate>"
        "<version>1.100000</version></info>"
    ).encode("utf-8")


def _samples_content(stream):
    timestamps = stream["timestamps"]
    channel_format = stream["channel_format"]
    buf = BytesIO()
    buf.write(_varlen_int(len(timestamps)))
    if channel_format == "string":
        for ts, row in zip(timestamps, stream["values"]):
            buf.write(b"\x08")
            buf.write(struct.pack("<d", float(ts)))
            for val in row:
                val_bytes = str(val).encode("utf-8")
                buf.write(_varlen_int(len(val_bytes)))
                buf.write(val_bytes)
    else:
        dtype = _NUMERIC_DTYPES[channel_format]
        arr = np.asarray(stream["values"], dtype=dtype)
        for i, ts in enumerate(timestamps):
            buf.write(b"\x08")
            buf.write(struct.pack("<d", float(ts)))
            buf.write(arr[i].tobytes())
    return buf.getvalue()


def write_xdf(path, streams):
    """Write a minimal-but-valid .xdf file readable by pyxdf.load_xdf.

    `streams` is a list of dicts, each with:
      id (int, unique), name (str), type (str, e.g. 'EEG'/'Markers'),
      channel_format ('double64' | 'float32' | 'string'), channel_count (int),
      nominal_srate (float), source_id (str),
      timestamps (1D sequence of float seconds),
      values (2D array-like [n_samples, channel_count] for numeric formats,
              or a list of length-channel_count row-lists of str for 'string').
    """
    with open(path, "wb") as f:
        f.write(b"XDF:")
        f.write(_chunk(1, '<?xml version="1.0"?><info><version>1.0</version></info>'.encode("utf-8")))

        for s in streams:
            header_xml = _stream_header_xml(
                s["name"], s["type"], s["channel_count"], s["channel_format"], s["nominal_srate"], s["source_id"]
            )
            f.write(_chunk(2, struct.pack("<I", s["id"]) + header_xml))

        for s in streams:
            f.write(_chunk(3, struct.pack("<I", s["id"]) + _samples_content(s)))

        for s in streams:
            n = len(s["timestamps"])
            first_ts = s["timestamps"][0] if n else 0.0
            last_ts = s["timestamps"][-1] if n else 0.0
            footer_xml = (
                '<?xml version="1.0"?><info>'
                f"<first_timestamp>{first_ts}</first_timestamp>"
                f"<last_timestamp>{last_ts}</last_timestamp>"
                f"<sample_count>{n}</sample_count></info>"
            ).encode("utf-8")
            f.write(_chunk(6, struct.pack("<I", s["id"]) + footer_xml))
