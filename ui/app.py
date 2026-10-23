import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import mss

from recorder.engine import ScreenRecorder, RecorderState
from recorder.storage import (
    get_default_recordings_dir,
    generate_recording_filename,
    list_recordings,
    open_in_system_explorer,
)


class ScreenRecorderApp(tk.Tk):
    DARK_BG = "#1e1e24"
    PANEL_BG = "#2b2b36"
    ACCENT_RED = "#e63946"
    ACCENT_GREEN = "#2a9d8f"
    ACCENT_BLUE = "#3a86ff"
    TEXT_LIGHT = "#f8f9fa"
    TEXT_MUTED = "#adb5bd"

    def __init__(self):
        super().__init__()
        self.title("Screen Recorder")
        self.geometry("680x560")
        self.minsize(620, 500)
        self.configure(bg=self.DARK_BG)

        self.recordings_dir = get_default_recordings_dir()
        self.recorder = None
        self.current_file = None

        self._setup_styles()
        self._build_ui()
        self._refresh_monitors()
        self._refresh_history()
        self._poll_status()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "TLabel",
            background=self.PANEL_BG,
            foreground=self.TEXT_LIGHT,
            font=("Helvetica", 10),
        )
        style.configure(
            "Header.TLabel",
            background=self.DARK_BG,
            foreground=self.TEXT_LIGHT,
            font=("Helvetica", 15, "bold"),
        )
        style.configure(
            "Status.TLabel",
            background=self.DARK_BG,
            foreground=self.ACCENT_GREEN,
            font=("Helvetica", 11, "bold"),
        )
        style.configure(
            "Timer.TLabel",
            background=self.PANEL_BG,
            foreground=self.TEXT_LIGHT,
            font=("Helvetica", 26, "bold"),
        )
        style.configure(
            "TCombobox",
            fieldbackground="#373746",
            background=self.PANEL_BG,
            foreground=self.TEXT_LIGHT,
        )
        style.configure(
            "Treeview",
            background="#252530",
            fieldbackground="#252530",
            foreground=self.TEXT_LIGHT,
            rowheight=24,
        )
        style.map("Treeview", background=[("selected", self.ACCENT_BLUE)])
        style.configure("Treeview.Heading", background="#373746", foreground=self.TEXT_LIGHT)

    def _build_ui(self):
        # Header Frame
        header_frame = tk.Frame(self, bg=self.DARK_BG, pady=12, padx=16)
        header_frame.pack(fill=tk.X)

        title = ttk.Label(header_frame, text="Python Screen Recorder", style="Header.TLabel")
        title.pack(side=tk.LEFT)

        self.status_label = ttk.Label(header_frame, text="● READY", style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT)

        # Control Panel
        panel = tk.Frame(self, bg=self.PANEL_BG, padx=16, pady=14, relief=tk.FLAT)
        panel.pack(fill=tk.X, padx=16, pady=4)

        # Config row
        cfg_row = tk.Frame(panel, bg=self.PANEL_BG)
        cfg_row.pack(fill=tk.X, pady=4)

        ttk.Label(cfg_row, text="Monitor:").pack(side=tk.LEFT, padx=(0, 6))
        self.monitor_combo = ttk.Combobox(cfg_row, state="readonly", width=18)
        self.monitor_combo.pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(cfg_row, text="FPS:").pack(side=tk.LEFT, padx=(0, 6))
        self.fps_combo = ttk.Combobox(cfg_row, state="readonly", width=6, values=["15", "30", "60"])
        self.fps_combo.set("30")
        self.fps_combo.pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(cfg_row, text="Folder:").pack(side=tk.LEFT, padx=(0, 6))
        self.folder_btn = tk.Button(
            cfg_row,
            text="Select Output",
            command=self._choose_directory,
            bg="#3c3f4e",
            fg=self.TEXT_LIGHT,
            relief=tk.FLAT,
            padx=8,
        )
        self.folder_btn.pack(side=tk.LEFT)

        # Timer display
        self.timer_label = ttk.Label(panel, text="00:00:00", style="Timer.TLabel")
        self.timer_label.pack(pady=10)

        # Buttons Row
        btn_row = tk.Frame(panel, bg=self.PANEL_BG)
        btn_row.pack(pady=4)

        self.record_btn = tk.Button(
            btn_row,
            text="▶ Start Recording",
            font=("Helvetica", 10, "bold"),
            bg=self.ACCENT_RED,
            fg="white",
            width=16,
            pady=6,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._on_record_clicked,
        )
        self.record_btn.pack(side=tk.LEFT, padx=6)

        self.pause_btn = tk.Button(
            btn_row,
            text="⏸ Pause",
            font=("Helvetica", 10, "bold"),
            bg="#555a6d",
            fg="white",
            width=12,
            pady=6,
            state=tk.DISABLED,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._on_pause_clicked,
        )
        self.pause_btn.pack(side=tk.LEFT, padx=6)

        self.open_dir_btn = tk.Button(
            btn_row,
            text="📁 Open Folder",
            font=("Helvetica", 10),
            bg="#3c3f4e",
            fg="white",
            width=12,
            pady=6,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: open_in_system_explorer(self.recordings_dir),
        )
        self.open_dir_btn.pack(side=tk.LEFT, padx=6)

        # History / Recordings List
        list_frame = tk.Frame(self, bg=self.DARK_BG, padx=16, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        list_header = tk.Frame(list_frame, bg=self.DARK_BG)
        list_header.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(list_header, text="Recent Recordings", style="Header.TLabel").pack(side=tk.LEFT)
        play_btn = tk.Button(
            list_header,
            text="Open Selected File",
            command=self._open_selected_recording,
            bg="#3a86ff",
            fg="white",
            relief=tk.FLAT,
            padx=8,
        )
        play_btn.pack(side=tk.RIGHT)

        cols = ("Filename", "Size (MB)", "Date")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("Filename", text="File Name")
        self.tree.heading("Size (MB)", text="Size (MB)")
        self.tree.heading("Date", text="Created Date")
        self.tree.column("Filename", width=300)
        self.tree.column("Size (MB)", width=90, anchor=tk.CENTER)
        self.tree.column("Date", width=140, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _refresh_monitors(self):
        with mss.mss() as sct:
            monitors = sct.monitors
            labels = []
            for i in range(1, len(monitors)):
                m = monitors[i]
                labels.append(f"Display {i} ({m['width']}x{m['height']})")
            if not labels and len(monitors) > 0:
                labels.append(f"All Monitors ({monitors[0]['width']}x{monitors[0]['height']})")
            self.monitor_combo["values"] = labels
            if labels:
                self.monitor_combo.current(0)

    def _choose_directory(self):
        new_dir = filedialog.askdirectory(initialdir=self.recordings_dir, title="Select Output Folder")
        if new_dir:
            self.recordings_dir = new_dir
            self._refresh_history()

    def _refresh_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        items = list_recordings(self.recordings_dir)
        for item in items:
            self.tree.insert("", tk.END, values=(item["name"], f"{item['size_mb']} MB", item["modified"]),
                             tags=(item["path"],))

    def _open_selected_recording(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select File", "Please select a recording from the table first.")
            return
        item = self.tree.item(selected[0])
        filename = item["values"][0]
        full_path = os.path.join(self.recordings_dir, filename)
        if os.path.exists(full_path):
            open_in_system_explorer(full_path)
        else:
            messagebox.showerror("File Missing", f"Could not find {filename}.")

    def _on_record_clicked(self):
        if self.recorder is None or self.recorder.get_state() in (RecorderState.STOPPED, RecorderState.IDLE):
            mon_idx = self.monitor_combo.current() + 1
            fps = int(self.fps_combo.get())
            self.current_file = generate_recording_filename(self.recordings_dir)
            self.recorder = ScreenRecorder(self.current_file, monitor_idx=mon_idx, fps=fps)
            self.recorder.start()

            self.record_btn.configure(text="■ Stop Recording", bg=self.ACCENT_RED)
            self.pause_btn.configure(state=tk.NORMAL, text="⏸ Pause", bg="#e76f51")
            self.monitor_combo.configure(state=tk.DISABLED)
            self.fps_combo.configure(state=tk.DISABLED)
            self.status_label.configure(text="● RECORDING", foreground=self.ACCENT_RED)
        else:
            # Stop recording
            self.recorder.stop()
            self.recorder = None
            self.record_btn.configure(text="▶ Start Recording", bg=self.ACCENT_RED)
            self.pause_btn.configure(state=tk.DISABLED, text="⏸ Pause", bg="#555a6d")
            self.monitor_combo.configure(state="readonly")
            self.fps_combo.configure(state="readonly")
            self.status_label.configure(text="● SAVED", foreground=self.ACCENT_BLUE)
            self._refresh_history()

    def _on_pause_clicked(self):
        if not self.recorder:
            return
        state = self.recorder.get_state()
        if state == RecorderState.RECORDING:
            self.recorder.pause()
            self.pause_btn.configure(text="▶ Resume", bg=self.ACCENT_GREEN)
            self.status_label.configure(text="❚❚ PAUSED", foreground="#f4a261")
        elif state == RecorderState.PAUSED:
            self.recorder.resume()
            self.pause_btn.configure(text="⏸ Pause", bg="#e76f51")
            self.status_label.configure(text="● RECORDING", foreground=self.ACCENT_RED)

    def _poll_status(self):
        if self.recorder:
            stats = self.recorder.get_stats()
            elapsed = int(stats["elapsed"])
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.timer_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.after(200, self._poll_status)
