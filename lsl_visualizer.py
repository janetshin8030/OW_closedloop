"""
Real-time LSL Stream Visualizer (optimized)

A standalone viewer that discovers and plots *every* LSL stream currently
on the network -- both continuous signal streams and event/marker streams. 

This version is optimized to:
- draw marker lines only on a single primary plot (instead of all plots)
- downsample plotted data
- reduce redraw frequency
- shorten history window
"""

from __future__ import annotations

import argparse
import time
from collections import deque
from itertools import count

import numpy as np
import pylsl
from pyqtgraph.Qt import QtCore, QtWidgets
import pyqtgraph as pg

MARKER_COLORS = ["r", "g", "b", "y", "m", "c", "w"]


def _channel_labels(info: pylsl.StreamInfo) -> list[str]:
    labels = []
    ch = info.desc().child("channels").child("channel")
    while ch.name() == "channel":
        label = ch.child_value("label") or ch.child_value("name")
        if label:
            labels.append(label)
        ch = ch.next_sibling()
    if len(labels) != info.channel_count():
        labels = [f"Ch{i + 1}" for i in range(info.channel_count())]
    return labels


class StreamHandle:
    """Wraps one LSL inlet plus its rolling sample buffers."""

    _next_color = count(0)

    def __init__(self, info: pylsl.StreamInfo):
        self.name = info.name()
        self.stype = info.type()
        self.channel_count = max(info.channel_count(), 1)
        self.is_marker = self.stype.lower() == "markers"
        self.channel_labels = _channel_labels(info)
        self.inlet = pylsl.StreamInlet(
            info, max_buflen=360, processing_flags=pylsl.proc_clocksync
        )
        self.times: deque[float] = deque()
        self.values: list[deque[float]] = [deque() for _ in range(self.channel_count)]
        self.color = MARKER_COLORS[next(StreamHandle._next_color) % len(MARKER_COLORS)]
        self.plot: pg.PlotItem | None = None
        self.curves: list[pg.PlotDataItem] = []
        self.marker_lines: deque[tuple[float, pg.GraphicsObject, pg.PlotItem]] = deque()
        self.alive = True


class LSLVisualizerWindow(QtWidgets.QMainWindow):
    def __init__(self, args: argparse.Namespace):
        super().__init__()
        self.args = args
        self.setWindowTitle("LSL Stream Visualizer (optimized: EEG + Markers)")
        self.resize(1100, 800)

        self.streams: dict[str, StreamHandle] = {}
        self.signal_plots_layout = pg.GraphicsLayoutWidget()

        self.log = QtWidgets.QPlainTextEdit(readOnly=True)
        self.log.setMaximumBlockCount(1000)
        self.log.setFixedHeight(180)

        self.status = QtWidgets.QLabel("Scanning for LSL streams...")

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        layout.addWidget(self.status)
        layout.addWidget(self.signal_plots_layout, stretch=1)
        layout.addWidget(QtWidgets.QLabel("Marker / event log:"))
        layout.addWidget(self.log)
        self.setCentralWidget(central)

        self._last_rescan = 0.0
        self._rescan()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(int(1000 / max(args.refresh_hz, 1.0)))

    def _log(self, text: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        self.log.appendPlainText(f"[{stamp}] {text}")

    def _rescan(self) -> None:
        infos = pylsl.resolve_streams(wait_time=1.0)
        seen_names = set()
        for info in infos:
            name = info.name()
            seen_names.add(name)
            if name in self.streams:
                continue
            try:
                handle = StreamHandle(info)
            except Exception as exc:  # defensive
                self._log(f"Failed to open stream '{name}': {exc}")
                continue
            self.streams[name] = handle
            if not handle.is_marker:
                self._add_signal_plot(handle)
            kind = "marker" if handle.is_marker else "signal"
            self._log(
                f"Connected to {kind} stream '{name}' "
                f"(type={handle.stype}, channels={handle.channel_count})"
            )

        for name, handle in list(self.streams.items()):
            if name not in seen_names and handle.alive:
                handle.alive = False
                self._log(f"Stream '{name}' is no longer available.")

        self._update_status()

    def _update_status(self) -> None:
        alive = [h for h in self.streams.values() if h.alive]
        signal_names = [h.name for h in alive if not h.is_marker]
        marker_names = [h.name for h in alive if h.is_marker]
        self.status.setText(
            f"Signal streams: {', '.join(signal_names) or 'none'}  |  "
            f"Marker streams: {', '.join(marker_names) or 'none'}"
        )

    def _add_signal_plot(self, handle: StreamHandle) -> None:
        plot = self.signal_plots_layout.addPlot(
            row=len([h for h in self.streams.values() if h.plot is not None]),
            col=0,
        )
        plot.setTitle(f"{handle.name} ({handle.stype})")
        plot.showGrid(x=True, y=False)
        plot.setLabel("bottom", "time", "s")
        spacing = self.args.amplitude
        ticks = [(-i * spacing, label) for i, label in enumerate(handle.channel_labels)]
        plot.getAxis("left").setTicks([ticks])
        handle.plot = plot
        handle.curves = [
            plot.plot(pen=pg.intColor(i, hues=max(handle.channel_count, 1)))
            for i in range(handle.channel_count)
        ]

    def _primary_plot(self) -> pg.PlotItem | None:
        # First non-marker signal plot
        for h in self.streams.values():
            if h.plot is not None and not h.is_marker and h.alive:
                return h.plot
        return None

    def _pull_samples(self, handle: StreamHandle) -> None:
        if not handle.alive:
            return
        try:
            # smaller chunks for visualization
            chunk, timestamps = handle.inlet.pull_chunk(timeout=0.0, max_samples=256)
        except pylsl.LostError:
            handle.alive = False
            self._log(f"Lost connection to stream '{handle.name}'.")
            self._update_status()
            return
        if not timestamps:
            return
        for sample, ts in zip(chunk, timestamps):
            handle.times.append(ts)
            for ch_i in range(handle.channel_count):
                value = sample[ch_i] if ch_i < len(sample) else float("nan")
                handle.values[ch_i].append(value)
            if handle.is_marker:
                self._on_marker(handle, ts, sample)

    def _on_marker(self, handle: StreamHandle, ts: float, sample) -> None:
        value = sample[0] if sample else ""
        self._log(f"{handle.name}: {value}")

        primary = self._primary_plot()
        if primary is None:
            return

        line = pg.InfiniteLine(
            pos=ts, angle=90, pen=pg.mkPen(handle.color, style=QtCore.Qt.DashLine)
        )
        text = pg.TextItem(str(value), color=handle.color, anchor=(0, 1))
        text.setPos(ts, 0)

        primary.addItem(line)
        primary.addItem(text)

        # Track only on the primary plot for trimming
        for h in self.streams.values():
            if h.plot is primary:
                h.marker_lines.append((ts, line, primary))
                h.marker_lines.append((ts, text, primary))
                break

    def _trim(self, handle: StreamHandle, now: float) -> None:
        cutoff = now - self.args.time_window - 2.0
        while handle.times and handle.times[0] < cutoff:
            handle.times.popleft()
            for values in handle.values:
                values.popleft()
        while handle.marker_lines and handle.marker_lines[0][0] < cutoff:
            _ts, item, plot = handle.marker_lines.popleft()
            plot.removeItem(item)

    def _update_signal_plot(self, handle: StreamHandle, now: float) -> None:
        if handle.plot is None or not handle.times:
            return
        x = np.fromiter(handle.times, dtype=float)
        # simple downsampling for performance
        x = x[::2]
        for i, curve in enumerate(handle.curves):
            y = np.fromiter(handle.values[i], dtype=float)[::2]
            y = y - i * self.args.amplitude   # shift each channel to its lane
            curve.setData(x=x, y=y)
        handle.plot.setXRange(now - self.args.time_window, now, padding=0)

    def _tick(self) -> None:
        now = pylsl.local_clock()
        if now - self._last_rescan >= self.args.rescan_interval:
            self._last_rescan = now
            self._rescan()

        for handle in list(self.streams.values()):
            self._pull_samples(handle)
            self._trim(handle, now)
            if not handle.is_marker:
                self._update_signal_plot(handle, now)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Optimized real-time visualizer for all active LSL streams (EEG + Markers)."
    )
    parser.add_argument(
        "--time-window",
        type=float,
        default=8.0,
        help="Seconds of history shown for signal streams (default: 8)",
    )
    parser.add_argument(
        "--rescan-interval",
        type=float,
        default=10.0,
        help="Seconds between scans for new/lost LSL streams (default: 10)",
    )
    parser.add_argument(
        "--amplitude",
        type=float,
        default=200.0,
        help="Vertical spacing between stacked channels within a signal plot (default: 30)",
    )
    parser.add_argument(
        "--refresh-hz",
        type=float,
        default=8.0,
        help="Plot redraw rate in Hz (default: 8)",
    )
    args = parser.parse_args()

    pg.setConfigOptions(
        antialias=True,
        background="k",
        foreground="w",
        useOpenGL=True,
    )

    app = QtWidgets.QApplication([])
    window = LSLVisualizerWindow(args)
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
