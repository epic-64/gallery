import logging
import os
import shutil
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Constants
SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png")
OUTPUT_FOLDER_NAME = "output"


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

                for item in folder_contents:
                    if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS and "#" not in item.stem:
                        # Move original back to root
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
                        restored_count += 1
                        logger.info(f"Restored: {item.name} -> {dest_path.name}")

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
