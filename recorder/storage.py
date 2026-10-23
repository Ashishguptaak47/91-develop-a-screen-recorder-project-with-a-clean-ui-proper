import os
import sys
import subprocess
from datetime import datetime


def get_default_recordings_dir():
    home = os.path.expanduser("~")
    videos = os.path.join(home, "Videos", "ScreenRecordings")
    try:
        os.makedirs(videos, exist_ok=True)
        return videos
    except OSError:
        local_dir = os.path.abspath("recordings")
        os.makedirs(local_dir, exist_ok=True)
        return local_dir


def generate_recording_filename(directory, extension="mp4"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"Recording_{timestamp}.{extension}"
    return os.path.join(directory, filename)


def list_recordings(directory):
    if not os.path.exists(directory):
        return []
    results = []
    valid_exts = (".mp4", ".avi", ".mkv")
    for fname in sorted(os.listdir(directory), reverse=True):
        if fname.lower().endswith(valid_exts):
            path = os.path.join(directory, fname)
            try:
                stat = os.stat(path)
                size_mb = stat.st_size / (1024 * 1024)
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                results.append({
                    "name": fname,
                    "path": path,
                    "size_mb": round(size_mb, 2),
                    "modified": modified
                })
            except OSError:
                continue
    return results


def open_in_system_explorer(target_path):
    path = os.path.abspath(target_path)
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)
