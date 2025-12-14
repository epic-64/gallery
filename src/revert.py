import logging
import os
import shutil
from pathlib import Path

try:
    from .constants import OUTPUT_FOLDER_NAME, SUPPORTED_EXTENSIONS
except ImportError:
    from constants import OUTPUT_FOLDER_NAME, SUPPORTED_EXTENSIONS

# Configure logging
logger = logging.getLogger(__name__)


def _is_stripped_file(stem: str, folder_number: str) -> bool:
    """Check if a file is a stripped/renamed file based on folder number.

    Stripped files will have the folder number at the START or END of the filename,
    separated by common separators. This avoids false positives from numbers appearing
    in the middle of original filenames.

    Args:
        stem: The filename stem (without extension)
        folder_number: The folder number to check for

    Returns:
        True if this is a stripped file, False if it's an original
    """
    # Common separators used in processing
    common_separators = [" ", "-", "_", "#", " #", " - ", "_", "-"]

    # Check for zero-padded versions (1-4 digits)
    padded_numbers = [folder_number.zfill(i) for i in range(1, 5)]

    for padded_num in padded_numbers:
        # Check if number is at the START (prefix mode)
        for sep in common_separators:
            if stem.startswith(padded_num + sep):
                return True

        # Check if number is at the END (suffix mode)
        for sep in common_separators:
            if stem.endswith(sep + padded_num):
                return True

        # Check if stem is just the number
        if stem == padded_num:
            return True

    return False


def _restore_original_file(item: Path, folder_path: Path) -> tuple[bool, str]:
    """Restore an original file to the root folder, handling name conflicts.

    Args:
        item: Path to the file to restore
        folder_path: Path to the root folder

    Returns:
        Tuple of (success, destination filename)
    """
    dest_path = folder_path / item.name

    # Handle name conflicts
    if dest_path.exists():
        base = item.stem
        ext = item.suffix
        counter = 1
        while dest_path.exists():
            dest_path = folder_path / f"{base}_{counter}{ext}"
            counter += 1
        logger.warning(f"Name conflict resolved: {item.name} -> {dest_path.name}")

    shutil.move(str(item), str(dest_path))
    logger.info(f"Restored: {item.name} -> {dest_path.name}")
    return True, dest_path.name


def revert_processing(folder: str) -> tuple[int, list[str]]:
    """Reverts the image processing by restoring original files and removing generated folders.

    This function:
    - Finds all numbered subfolders containing original images
    - Moves original images back to the root folder
    - Removes numbered subfolders and their contents
    - Removes the output folder

    Args:
        folder: The root folder where processing was done

    Returns:
        Tuple of (number of files restored, list of error messages)
    """
    folder_path = Path(folder)
    restored_count = 0
    errors = []

    try:
        # Find all numbered folders
        numbered_folders = [
            folder_path / name for name in os.listdir(folder) if name.isdigit() and (folder_path / name).is_dir()
        ]

        logger.info(f"Found {len(numbered_folders)} numbered folder(s) to process")

        # Process each numbered folder
        for num_folder in numbered_folders:
            try:
                # Find original image files (excluding info.txt and stripped versions)
                folder_contents = list(num_folder.iterdir())
                folder_number = num_folder.name

                for item in folder_contents:
                    # Skip if not an image file
                    if not (item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS):
                        continue

                    # Skip files that are stripped versions
                    if _is_stripped_file(item.stem, folder_number):
                        logger.debug(f"Skipping stripped file: {item.name}")
                        continue

                    # This is an original file, restore it
                    _restore_original_file(item, folder_path)
                    restored_count += 1

                # Remove the numbered folder and all its contents
                shutil.rmtree(num_folder)
                logger.info(f"Removed folder: {num_folder}")

            except Exception as e:
                error_msg = f"Error processing folder {num_folder}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Remove output folder if it exists
        output_folder = folder_path / OUTPUT_FOLDER_NAME
        if output_folder.exists() and output_folder.is_dir():
            try:
                shutil.rmtree(output_folder)
                logger.info(f"Removed output folder: {output_folder}")
            except Exception as e:
                error_msg = f"Error removing output folder: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        return restored_count, errors

    except Exception as e:
        error_msg = f"Error during revert: {e}"
        logger.error(error_msg, exc_info=True)
        errors.append(error_msg)
        return restored_count, errors
