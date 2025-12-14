"""Tests for the revert functionality."""

import os
import shutil
from pathlib import Path

import pytest
from PIL import Image

from src.constants import INFO_FILENAME, OUTPUT_FOLDER_NAME, SUPPORTED_EXTENSIONS
from src.process import process_images
from src.revert import _is_stripped_file, revert_processing


class TestIsStrippedFile:
    """Tests for the _is_stripped_file function."""

    def test_prefix_mode_with_space_separator(self):
        """Test stripped file in prefix mode with space separator."""
        assert _is_stripped_file("001 basename", "1") is True
        assert _is_stripped_file("1 basename", "1") is True

    def test_suffix_mode_with_space_separator(self):
        """Test stripped file in suffix mode with space separator."""
        assert _is_stripped_file("basename 001", "1") is True
        assert _is_stripped_file("basename 1", "1") is True

    def test_prefix_mode_with_hash_separator(self):
        """Test stripped file with hash separator."""
        assert _is_stripped_file("001#basename", "1") is True
        assert _is_stripped_file("basename #001", "1") is True

    def test_prefix_mode_with_dash_separator(self):
        """Test stripped file with dash separator."""
        assert _is_stripped_file("001-basename", "1") is True
        assert _is_stripped_file("basename-001", "1") is True

    def test_just_the_number(self):
        """Test when filename is just the number."""
        assert _is_stripped_file("001", "1") is True
        assert _is_stripped_file("1", "1") is True

    def test_original_filename_with_numbers_in_middle(self):
        """Test that original filenames with numbers in the middle are not falsely identified as stripped."""
        # This is the bug we're fixing - "00127-1000473567" should NOT match folder "1"
        assert _is_stripped_file("00127-1000473567", "1") is False
        assert _is_stripped_file("image-123-456", "1") is False
        assert _is_stripped_file("photo_2024_01_15", "1") is False
        assert _is_stripped_file("IMG_1234", "1") is False

    def test_original_filename_that_ends_with_different_number(self):
        """Test original filenames that end with numbers different from folder number."""
        assert _is_stripped_file("image-123", "1") is False
        assert _is_stripped_file("photo 456", "1") is False

    def test_zero_padded_matching(self):
        """Test that zero-padded numbers are correctly matched."""
        assert _is_stripped_file("basename 001", "1") is True
        assert _is_stripped_file("basename 0001", "1") is True
        assert _is_stripped_file("001 basename", "1") is True
        assert _is_stripped_file("0001 basename", "1") is True

    def test_multiple_digit_folder_numbers(self):
        """Test with folder numbers that have multiple digits."""
        assert _is_stripped_file("basename 042", "42") is True
        assert _is_stripped_file("042 basename", "42") is True
        assert _is_stripped_file("basename-42", "42") is True
        assert _is_stripped_file("00142-1000473567", "42") is False


class TestRevertProcessing:
    """Integration tests for revert_processing function."""

    @pytest.fixture
    def temp_folder(self, tmp_path):
        """Create a temporary folder for testing."""
        return tmp_path / "test_images"

    @pytest.fixture
    def sample_image(self, temp_folder):
        """Create a sample image file."""
        temp_folder.mkdir(parents=True, exist_ok=True)
        img_path = temp_folder / "test_image.jpg"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(str(img_path))
        return img_path

    def test_revert_with_problematic_filename(self, temp_folder):
        """Test revert doesn't delete originals with numbers in their names."""
        temp_folder.mkdir(parents=True, exist_ok=True)

        # Create an image with a problematic filename
        original_name = "00127-1000473567.jpg"
        img_path = temp_folder / original_name
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(str(img_path))

        # Process the image
        base_name = "test"
        processed_count, errors = process_images(str(temp_folder), base_name, "suffix", " #", 3)
        assert processed_count == 1
        assert len(errors) == 0

        # Verify the structure after processing
        numbered_folder = temp_folder / "1"
        assert numbered_folder.exists()
        assert (numbered_folder / original_name).exists()
        assert (numbered_folder / INFO_FILENAME).exists()

        # Find the stripped file
        stripped_files = [
            f for f in numbered_folder.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS and f.name != original_name
        ]
        assert len(stripped_files) == 1

        # Now revert
        restored_count, errors = revert_processing(str(temp_folder))
        assert len(errors) == 0
        assert restored_count == 1

        # Verify the original file was restored
        assert (temp_folder / original_name).exists()
        assert not numbered_folder.exists()

    def test_revert_multiple_images_with_numbers_in_names(self, temp_folder):
        """Test reverting multiple images with numbers in their names."""
        temp_folder.mkdir(parents=True, exist_ok=True)

        # Create multiple images with problematic filenames
        filenames = [
            "00127-1000473567.jpg",
            "IMG_1234_edited.jpg",
            "photo-2024-01-15.jpg",
            "scan_001_page1.jpg",
        ]

        for filename in filenames:
            img_path = temp_folder / filename
            img = Image.new("RGB", (100, 100), color="green")
            img.save(str(img_path))

        # Process all images
        base_name = "processed"
        processed_count, errors = process_images(str(temp_folder), base_name, "suffix", " - ", 3)
        assert processed_count == len(filenames)
        assert len(errors) == 0

        # Verify numbered folders were created
        for i in range(1, len(filenames) + 1):
            numbered_folder = temp_folder / str(i)
            assert numbered_folder.exists()

        # Revert
        restored_count, errors = revert_processing(str(temp_folder))
        assert len(errors) == 0
        assert restored_count == len(filenames)

        # Verify all original files were restored
        for filename in filenames:
            assert (temp_folder / filename).exists()

        # Verify numbered folders were removed
        for i in range(1, len(filenames) + 1):
            numbered_folder = temp_folder / str(i)
            assert not numbered_folder.exists()
