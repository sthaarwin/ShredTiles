import sys

import mido

from src.app import App


def main():
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("  Path to MIDI file: ").strip() or "your_song.mid"

    try:
        mid = mido.MidiFile(file_path)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading MIDI: {e}")
        sys.exit(1)

    app = App(file_path, mid)
    app.run()


if __name__ == "__main__":
    main()
