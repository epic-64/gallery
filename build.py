#!/usr/bin/env python3
"""
Universal build script for creating standalone executables.
Works on Windows, Linux, and macOS.

Usage:
    python build.py              # Build for current platform
    python build.py --clean      # Clean build artifacts and rebuild
    python build.py --onedir     # Create one-directory bundle instead of one-file
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def print_header(message):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(message)
    print("=" * 60 + "\n")


def check_pyinstaller():
    """Check if PyInstaller is installed, install if not."""
    try:
        import PyInstaller

        print(f"✓ PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0.0"])
            print("✓ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install PyInstaller")
            return False


def clean_build_artifacts():
    """Remove previous build artifacts."""
    print("Cleaning previous build artifacts...")

    dirs_to_remove = ["build", "dist", "__pycache__"]

    project_root = Path(__file__).parent

    for dir_name in dirs_to_remove:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_name}/")

    # Remove .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        pyc_file.unlink()

    print("✓ Cleanup complete\n")


def build_executable(onedir=False):
    """Build the executable using PyInstaller."""
    system = platform.system().lower()

    print_header(f"Building Woop for {platform.system()}")

    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Architecture: {platform.machine()}\n")

    # Check PyInstaller
    if not check_pyinstaller():
        return False

    print("\nBuilding executable...")
    print("This may take a few minutes...\n")

    try:
        # Use the spec file for consistent builds
        cmd = [sys.executable, "-m", "PyInstaller", "woop.spec", "--noconfirm"]

        # Show build progress
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1
        )

        # Print output in real-time
        if process.stdout:
            for line in process.stdout:
                print(line, end="")

        process.wait()

        if process.returncode != 0:
            print("\n✗ Build failed!")
            return False

        # Verify the executable was created
        exe_path = Path("dist/woop.exe") if system == "windows" else Path("dist/woop")

        if not exe_path.exists():
            print(f"\n✗ Executable not found at {exe_path}")
            return False

        # Make executable on Unix systems
        if system != "windows":
            exe_path.chmod(0o755)

        print_header("Build Successful!")

        print(f"✓ Executable created: {exe_path.absolute()}")
        print(f"✓ Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB\n")

        print("Distribution:")
        print("  • The executable is standalone")
        print("  • No Python installation required on target machine")
        print("  • Can be copied/moved anywhere")

        if system == "windows":
            print("  • Run by double-clicking woop.exe")
        else:
            print("  • Run with: ./woop")
            print(f"  • Only works on {platform.system()} with compatible system libraries")

        print("\nTesting executable...")
        try:
            # Quick test that it runs
            test_process = subprocess.Popen(
                [str(exe_path), "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            test_process.wait(timeout=5)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # GUI app might not respond to --version, that's okay
            print("  Note: Executable created but cannot verify startup")
            print("  (This is normal for GUI applications)")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed with error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build standalone executable for Woop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py              # Build for current platform
  python build.py --clean      # Clean and rebuild
  python build.py --onedir     # Create directory bundle
        """,
    )

    parser.add_argument("--clean", action="store_true", help="Clean build artifacts before building")

    parser.add_argument(
        "--onedir", action="store_true", help="Create one-directory bundle instead of one-file executable"
    )

    args = parser.parse_args()

    # Change to script directory
    script_dir = Path(__file__).parent
    import os

    os.chdir(script_dir)

    # Clean if requested
    if args.clean:
        clean_build_artifacts()

    # Build
    success = build_executable(onedir=args.onedir)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
