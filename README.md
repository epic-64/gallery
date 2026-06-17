# woop

A small desktop GUI for **batch-renaming and organizing image files**. Point it at a
folder, give your photos a common base name, and woop renames them with consistent,
zero-padded numbering — preserving EXIF metadata and keeping the originals safe.

Built with Python and Tkinter; runs on Windows, macOS, and Linux.

## Features

- 📁 Batch-rename every image in a folder with a shared base name
- 🔢 Prefix or suffix numbering with a configurable separator and zero-padding
- 👀 Live filename preview before you commit
- 🖼️ Built-in image preview and review panels
- 🧷 EXIF metadata is preserved during processing
- ↩️ Revert a processing run to restore the original filenames
- 💾 Remembers your settings between sessions (`~/.woop/woop_config.json`)

Supported formats: `.jpg`, `.jpeg`, `.png`.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```bash
git clone <repository-url>
cd woop

# With uv (recommended)
uv sync

# Or with pip
pip install -e .
```

## Usage

**On Windows**, just double-click `woop.bat` — on first run it sets up the
environment automatically and then launches the app. (It uses [uv](https://docs.astral.sh/uv/);
if uv isn't installed, the script tells you the one-line command to install it.)

From a terminal, run it any of these ways:

```bash
python -m woop      # as a module
python run.py       # via the entry script
woop                # console script (after pip install -e .)
```

A folder picker opens on startup. Choose a folder of images, set your base name and
numbering options, preview the result, and run. Processed images are written to an
`_output` subfolder so your originals are never overwritten in place.

## Development

```bash
# Run the test suite
pytest tests/

# With a coverage report
pytest tests/ --cov=woop --cov-report=html

# Lint and format
ruff check woop/ tests/
ruff format woop/ tests/
```

The current tests cover the core processing (`test_process.py`) and revert
(`test_revert.py`) logic.

## Building a standalone executable

`build.py` produces a single-file, self-contained executable for the current
platform using PyInstaller (no Python required on the target machine):

```bash
python build.py            # build for the current platform
python build.py --clean    # clean artifacts, then build
python build.py --onedir   # one-directory bundle instead of one file
```

The executable is written to `dist/` (`woop.exe` on Windows, `woop` elsewhere).

## Project structure

```
woop/
├── woop/             # Application package
│   ├── __main__.py   # `python -m woop` entry point
│   ├── main.py       # GUI and application wiring
│   ├── process.py    # Image renaming / processing
│   ├── revert.py     # Restore original filenames
│   ├── preview.py    # Image preview panel
│   ├── review.py     # Review window
│   ├── config.py     # Persisted user settings
│   └── constants.py  # Shared constants
├── tests/            # Test suite
├── build.py          # Cross-platform executable builder
├── woop.spec         # PyInstaller spec
├── run.py            # Simple entry-point script
└── pyproject.toml
```

## License

Released under the [MIT License](LICENSE).
