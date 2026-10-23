# Python Screen Recorder

A modern, lightweight desktop screen recorder built with Python, Tkinter, `mss`, and OpenCV. Features a clean dark interface, multiple monitor selection, adjustable FPS, recording timer, pause/resume capability, and an integrated recordings manager.

## Features
- **Clean Dark UI**: Native Tkinter interface styled with modern dark accents.
- **Multi-Monitor Support**: Automatically enumerates connected displays.
- **High Performance**: Low-overhead screen capture powered by `mss` and `OpenCV`.
- **Pause & Resume**: Seamlessly pause and resume recordings without restarting.
- **Built-in Recording Manager**: Browse, inspect file sizes, and open recorded videos directly from the UI.
- **Configurable Settings**: Choose output directory, target FPS (15, 30, 60), and target screen.

## Installation

```bash
git clone <repo-url>
cd screen-recorder
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

## Running Tests

```bash
pytest
```
