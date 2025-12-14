import logging
import os
import shutil
from pathlib import Path

import piexif  # type: ignore
from PIL import Image  # type: ignore

# Configure logging
logger = logging.getLogger(__name__)

# Constants
SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png")
INFO_FILENAME = "info.txt"
OUTPUT_FOLDER_NAME = "output"
DEFAULT_JPEG_QUALITY = 100


def get_image_files(folder: str) -> list[str]:
    """Returns a list of image files sorted by creation date (oldest first).

    Args:
        folder: Path to the folder containing images

    Returns:
        List of image filenames sorted by creation date
    """
    try:
        folder_path = Path(folder)
        image_files = [f for f in os.listdir(folder) if f.lower().endswith(SUPPORTED_EXTENSIONS)]

        def get_creation_time(filename):
            try:
                stat = (folder_path / filename).stat()
                # Use birth time (creation time) on Windows, or fallback to modification time
                return getattr(stat, "st_birthtime", stat.st_mtime)
            except Exception:
                return 0

        return sorted(image_files, key=get_creation_time)
    except OSError as e:
        logger.error(f"Error reading folder {folder}: {e}")
        return []


def get_existing_numbered_folders(folder: str, needed_count: int) -> list[str]:
    """Gets or creates numbered folders for organizing images.

    Reuses empty numbered folders if available, otherwise creates new ones.

    Args:
        folder: Parent folder path
        needed_count: Number of folders needed

    Returns:
        List of folder paths
    """
    try:
        # Find all existing numeric folders
        folder_path = Path(folder)
        existing_numeric_folders = {
            int(name): str(folder_path / name)
            for name in os.listdir(folder)
            if name.isdigit() and (folder_path / name).is_dir()
        }

        used_numbers = sorted(existing_numeric_folders.keys())
        numbered = []

        # Reuse empty folders in order
        for number in used_numbers:
            path = existing_numeric_folders[number]
            if not os.listdir(path):  # empty folder
                numbered.append(path)
                logger.debug(f"Reusing empty folder: {path}")
                if len(numbered) == needed_count:
                    return numbered

        # Continue with next number after the last used
        next_number = used_numbers[-1] + 1 if used_numbers else 1
        while len(numbered) < needed_count:
            path = str(folder_path / str(next_number))
            os.makedirs(path, exist_ok=True)
            numbered.append(path)
            logger.debug(f"Created new folder: {path}")
            next_number += 1

        return numbered
    except OSError as e:
        logger.error(f"Error creating numbered folders: {e}")
        raise


def decode_exif_user_comment(raw: bytes) -> str:
    """Decodes EXIF UserComment field from various encoding formats.

    Supports ASCII, JIS (Shift-JIS), UNICODE (UTF-16-BE), and UTF-8 encodings.

    Args:
        raw: Raw bytes from EXIF UserComment field

    Returns:
        Decoded string comment
    """
    if raw.startswith(b"ASCII\x00\x00\x00"):
        return raw[8:].decode("ascii", errors="ignore")
    elif raw.startswith(b"JIS\x00\x00\x00"):
        return raw[8:].decode("shift_jis", errors="ignore")
    elif raw.startswith(b"UNICODE\x00\x00"):
        return raw[8:].decode("utf-16-be", errors="ignore")  # no BOM!
    elif raw.startswith(b"\x00" * 8):
        return raw[8:].decode("utf-8", errors="ignore")
    else:
        # Guess fallback
        try:
            return raw.decode("utf-8", errors="ignore")
        except UnicodeDecodeError:
            logger.warning(f"Could not decode EXIF comment, {len(raw)} bytes")
            return f"[binary: {len(raw)} bytes]"


def extract_exif(img_path: str) -> dict[str, str]:
    """Extracts EXIF UserComment from an image file.

    Args:
        img_path: Path to the image file

    Returns:
        Dictionary containing UserComment or Error message
    """
    try:
        exif_dict = piexif.load(img_path)
        user_comment_raw = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)

        if not user_comment_raw:
            logger.debug(f"No UserComment found in {img_path}")
            return {"UserComment": "[not present]"}

        comment = decode_exif_user_comment(user_comment_raw)
        return {"UserComment": comment.strip()}

    except FileNotFoundError:
        logger.error(f"Image file not found: {img_path}")
        return {"Error": "File not found"}
    except Exception as e:
        logger.error(f"Error extracting EXIF from {img_path}: {e}")
        return {"Error": str(e)}


def write_exif_to_file(exif_data: dict[str, str], target_path: str) -> None:
    """Writes EXIF data to a text file.

    Args:
        exif_data: Dictionary of EXIF data
        target_path: Path to the output text file
    """
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            for k, v in exif_data.items():
                f.write(f"{k}: {v}\n")
        logger.debug(f"Wrote EXIF data to {target_path}")
    except OSError as e:
        logger.error(f"Error writing EXIF file {target_path}: {e}")
        raise


def remove_exif_and_save(img_path: str, target_path: str) -> None:
    """Removes EXIF data from an image and saves it to a new location.

    Args:
        img_path: Source image path
        target_path: Destination image path
    """
    try:
        with Image.open(img_path) as img:
            img_format = img.format.upper() if img.format else "JPEG"
            icc_profile = img.info.get("icc_profile")

            # Save based on format
            if img_format in ("JPEG", "JPG"):
                img.save(
                    target_path,
                    format="JPEG",
                    quality=DEFAULT_JPEG_QUALITY,
                    optimize=False,
                    icc_profile=icc_profile,
                )
            elif img_format == "PNG":
                img.save(target_path, format="PNG", optimize=True)
            else:
                # Fallback: save using original format, best effort
                logger.warning(f"Unsupported format {img_format}, attempting to save anyway")
                img.save(target_path, format=img_format)

        logger.debug(f"Saved stripped image to {target_path}")
    except Exception as e:
        logger.error(f"Error processing image {img_path}: {e}")
        raise


def process_images(image_folder: str, base_name: str) -> tuple[int, list[str]]:
    """Process images by extracting EXIF, creating stripped copies, and organizing into folders.

    Args:
        image_folder: Path to folder containing images
        base_name: Base filename for renamed images

    Returns:
        Tuple of (number of images processed, list of error messages)
    """
    processed_count = 0
    errors = []

    try:
        # Get image files
        images = get_image_files(image_folder)
        if not images:
            logger.warning(f"No images found in {image_folder}")
            return 0, ["No images found in selected folder."]

        logger.info(f"Found {len(images)} image(s) to process")

        # Create output folder
        output_folder = os.path.join(image_folder, OUTPUT_FOLDER_NAME)
        os.makedirs(output_folder, exist_ok=True)
        logger.info(f"Output folder: {output_folder}")

        # Get numbered folders
        numbered_folders = get_existing_numbered_folders(image_folder, len(images))

        # Process each image
        for i, image_file in enumerate(images):
            try:
                logger.info(f"Processing {i + 1}/{len(images)}: {image_file}")

                original_path = os.path.join(image_folder, image_file)
                folder_path = numbered_folders[i]
                new_original_path = os.path.join(folder_path, image_file)

                # Move original to numbered folder
                shutil.move(original_path, new_original_path)

                # Extract and write EXIF data
                exif_data = extract_exif(new_original_path)
                info_file_path = os.path.join(folder_path, INFO_FILENAME)
                write_exif_to_file(exif_data, info_file_path)

                # Create stripped version with new name
                folder_number = os.path.basename(folder_path)
                ext = os.path.splitext(image_file)[1].lower()
                new_name = f"{base_name} #{folder_number}{ext}"
                stripped_path = os.path.join(folder_path, new_name)
                remove_exif_and_save(new_original_path, stripped_path)

                # Copy to output folder
                shutil.copy(stripped_path, os.path.join(output_folder, new_name))

                logger.info(f"Successfully processed: {new_name}")
                processed_count += 1

            except Exception as e:
                error_msg = f"Failed to process {image_file}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        logger.info("Image processing completed successfully")
        return processed_count, errors

    except Exception as e:
        error_msg = f"Unexpected error during processing: {e}"
        logger.error(error_msg, exc_info=True)
        errors.append(error_msg)
        return processed_count, errors
