import os
import time
import threading
from enum import Enum
import cv2
import numpy as np
import mss


class RecorderState(Enum):
    IDLE = "IDLE"
    RECORDING = "RECORDING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class ScreenRecorder:
    def __init__(self, output_filepath, monitor_idx=1, fps=30):
        self.output_filepath = output_filepath
        self.monitor_idx = monitor_idx
        self.fps = fps
        self.state = RecorderState.IDLE

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._thread = None
        self.elapsed_seconds = 0.0
        self.frames_captured = 0
        self._lock = threading.Lock()

    def get_state(self):
        with self._lock:
            return self.state

    def get_stats(self):
        with self._lock:
            return {
                "state": self.state,
                "elapsed": self.elapsed_seconds,
                "frames": self.frames_captured,
            }

    def start(self):
        if self.state != RecorderState.IDLE:
            return False
        self._stop_event.clear()
        self._pause_event.clear()
        self.state = RecorderState.RECORDING
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        return True

    def pause(self):
        with self._lock:
            if self.state == RecorderState.RECORDING:
                self.state = RecorderState.PAUSED
                self._pause_event.set()
                return True
        return False

    def resume(self):
        with self._lock:
            if self.state == RecorderState.PAUSED:
                self.state = RecorderState.RECORDING
                self._pause_event.clear()
                return True
        return False

    def stop(self):
        if self.state in (RecorderState.RECORDING, RecorderState.PAUSED):
            self._stop_event.set()
            self._pause_event.clear()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=3.0)
            with self._lock:
                self.state = RecorderState.STOPPED
            return True
        return False

    def _record_loop(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.output_filepath)), exist_ok=True)
        frame_interval = 1.0 / max(1, self.fps)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = None

        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                chosen_idx = self.monitor_idx if 0 < self.monitor_idx < len(monitors) else 1
                monitor = monitors[chosen_idx]
                width = int(monitor["width"])
                height = int(monitor["height"])

                writer = cv2.VideoWriter(
                    self.output_filepath,
                    fourcc,
                    float(self.fps),
                    (width, height),
                )

                last_frame_time = time.time()
                while not self._stop_event.is_set():
                    loop_start = time.time()

                    if self._pause_event.is_set():
                        time.sleep(0.05)
                        last_frame_time = time.time()
                        continue

                    img = sct.grab(monitor)
                    frame = np.array(img)
                    # Convert BGRA to BGR
                    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    writer.write(bgr_frame)

                    now = time.time()
                    delta = now - last_frame_time
                    last_frame_time = now

                    with self._lock:
                        self.elapsed_seconds += delta
                        self.frames_captured += 1

                    compute_time = time.time() - loop_start
                    sleep_time = frame_interval - compute_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        finally:
            if writer is not None:
                writer.release()
