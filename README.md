# Woop - Image Processing Tool

A modern image processing application with GUI for batch renaming and organizing images.

## Installation

```bash
# Clone the repository
cd C:\Users\epic-64\PyCharmProjects\woop

# Install dependencies (using uv or pip)
uv sync
# or
pip install -e .
```

## Running the Application

There are several ways to run the application:

### Option 1: Using the run script (Recommended)
```bash
python run.py
```

### Option 2: As a Python module
```bash
python -m woop
```

### Option 3: Using PyCharm
Simply select one of the pre-configured run configurations:
- **Woop** - Runs using `run.py`
- **Woop (Module)** - Runs using `python -m woop`

### Option 4: After installation as CLI tool
```bash
pip install -e .
woop
```

## ⚠️ Important: Do NOT run files directly

**Don't do this:**
```bash
python woop/main.py  # ❌ This will fail with ImportError
```

**Always use one of the proper entry points above** to ensure the package imports work correctly.

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Running Tests with Coverage
```bash
pytest tests/ --cov=woop --cov-report=html
```

### Code Quality
```bash
# Run linter
ruff check woop/ tests/

# Auto-fix issues
ruff check --fix woop/ tests/

# Format code
ruff format woop/ tests/
```

## Project Structure

```
woop/
├── woop/              # Main package
│   ├── __init__.py
│   ├── __main__.py    # Entry point for python -m woop
│   ├── main.py        # Main application logic
│   ├── config.py      # Configuration management
│   ├── constants.py   # Constants and settings
│   ├── preview.py     # Preview panel
│   ├── process.py     # Image processing logic
│   ├── revert.py      # Revert processing logic
│   └── review.py      # Review window
├── tests/             # Test suite
├── run.py             # Simple entry point script
├── pyproject.toml     # Project configuration
└── README.md          # This file
```

## Features

- 📁 Batch rename images with customizable numbering
- 🔢 Prefix or suffix numbering modes
- 🖼️ Image preview panel
- ↩️ Revert processing to restore original filenames
- 🎨 Modern GUI with Tkinter
- ✅ Comprehensive test suite

## License

Add your license here.

