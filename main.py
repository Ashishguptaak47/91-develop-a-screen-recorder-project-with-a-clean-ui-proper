import sys
from ui.app import ScreenRecorderApp


def main():
    app = ScreenRecorderApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
