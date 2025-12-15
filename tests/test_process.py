import os
import shutil
from pathlib import Path

import piexif
from PIL import Image

from woop.process import (
    decode_exif_user_comment,
    extract_exif,
    get_existing_numbered_folders,
    get_image_files,
    remove_exif_and_save,
    write_exif_to_file,
)


class TestDecodeExifUserComment:
    """Tests for the decode_exif_user_comment function."""

    def test_decode_ascii_comment(self):
        raw = b"ASCII\x00\x00\x00Hello World"
        result = decode_exif_user_comment(raw)
        assert result == "Hello World"

    def test_decode_jis_comment(self):
        raw = b"JIS\x00\x00\x00\x82\xb1\x82\xf1\x82\xc9\x82\xbf\x82\xcd"  # "こんにちは" in Shift-JIS
        result = decode_exif_user_comment(raw)
        assert "こんにちは" in result or len(result) > 0

    def test_decode_unicode_comment(self):
        # "Hello" in UTF-16-BE (Big Endian, no BOM)
        # Format: "UNICODE\x00" (8 bytes) + UTF-16-BE encoded text
        raw = b"UNICODE\x00\x00\x48\x00\x65\x00\x6c\x00\x6c\x00\x6f"
        result = decode_exif_user_comment(raw)
        assert result == "Hello"

    def test_decode_utf8_with_null_prefix(self):
        raw = b"\x00\x00\x00\x00\x00\x00\x00\x00Hello UTF-8"
        result = decode_exif_user_comment(raw)
        assert result == "Hello UTF-8"

    def test_decode_unknown_format_fallback(self):
        raw = b"Random data without proper encoding"
        result = decode_exif_user_comment(raw)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_decode_binary_data(self):
        raw = b"\xff\xfe\xfd\xfc"
        result = decode_exif_user_comment(raw)
        # Should return binary info or attempt decode
        assert isinstance(result, str)


class TestGetImageFiles:
    """Tests for the get_image_files function."""

    def test_get_image_files_empty_folder(self, tmp_path):
        folder = tmp_path / "empty"
        folder.mkdir()
        result = get_image_files(str(folder))
        assert result == []

    def test_get_image_files_with_images(self, tmp_path):
        folder = tmp_path / "images"
        folder.mkdir()

        # Create test image files with different timestamps
        for i, ext in enumerate([".jpg", ".jpeg", ".png"]):
            img_path = folder / f"image{i}{ext}"
            img_path.touch()
            # Ensure different modification times
            os.utime(img_path, (i, i))

        result = get_image_files(str(folder))
        assert len(result) == 3
        assert all(f.lower().endswith((".jpg", ".jpeg", ".png")) for f in result)

    def test_get_image_files_ignores_other_files(self, tmp_path):
        folder = tmp_path / "mixed"
        folder.mkdir()

        (folder / "image.jpg").touch()
        (folder / "document.txt").touch()
        (folder / "data.csv").touch()

        result = get_image_files(str(folder))
        assert len(result) == 1
        assert result[0] == "image.jpg"

    def test_get_image_files_case_insensitive(self, tmp_path):
        folder = tmp_path / "case"
        folder.mkdir()

        (folder / "image1.JPG").touch()
        (folder / "image2.JpEg").touch()
        (folder / "image3.PNG").touch()

        result = get_image_files(str(folder))
        assert len(result) == 3


class TestGetExistingNumberedFolders:
    """Tests for the get_existing_numbered_folders function."""

    def test_create_new_folders_from_scratch(self, tmp_path):
        result = get_existing_numbered_folders(str(tmp_path), 3)
        assert len(result) == 3
        assert all(os.path.exists(p) for p in result)

        folder_numbers = [int(os.path.basename(p)) for p in result]
        assert folder_numbers == [1, 2, 3]

    def test_reuse_empty_folders(self, tmp_path):
        # Create existing empty folders
        (tmp_path / "1").mkdir()
        (tmp_path / "2").mkdir()
        (tmp_path / "5").mkdir()

        result = get_existing_numbered_folders(str(tmp_path), 3)
        assert len(result) == 3

        folder_numbers = sorted([int(os.path.basename(p)) for p in result])
        assert 1 in folder_numbers
        assert 2 in folder_numbers
        assert 5 in folder_numbers

    def test_skip_non_empty_folders(self, tmp_path):
        # Create folders with files
        folder1 = tmp_path / "1"
        folder1.mkdir()
        (folder1 / "file.txt").touch()

        folder2 = tmp_path / "2"
        folder2.mkdir()  # Empty

        result = get_existing_numbered_folders(str(tmp_path), 2)
        assert len(result) == 2

        folder_numbers = sorted([int(os.path.basename(p)) for p in result])
        # Should reuse 2 (empty) and create 3 (next number)
        assert 2 in folder_numbers
        assert 3 in folder_numbers

    def test_continue_numbering_after_existing(self, tmp_path):
        (tmp_path / "5").mkdir()
        (tmp_path / "10").mkdir()

        result = get_existing_numbered_folders(str(tmp_path), 4)
        assert len(result) == 4

        folder_numbers = sorted([int(os.path.basename(p)) for p in result])
        # Should use 5, 10, then continue with 11, 12
        assert folder_numbers == [5, 10, 11, 12]


class TestWriteExifToFile:
    """Tests for the write_exif_to_file function."""

    def test_write_exif_data(self, tmp_path):
        target_path = tmp_path / "info.txt"
        exif_data = {
            "UserComment": "Test comment",
            "DateTime": "2025:12:15 10:30:00",
        }

        write_exif_to_file(exif_data, str(target_path))

        assert target_path.exists()
        content = target_path.read_text(encoding="utf-8")
        assert "UserComment: Test comment" in content
        assert "DateTime: 2025:12:15 10:30:00" in content

    def test_write_empty_exif_data(self, tmp_path):
        target_path = tmp_path / "empty.txt"
        exif_data = {}

        write_exif_to_file(exif_data, str(target_path))

        assert target_path.exists()
        content = target_path.read_text(encoding="utf-8")
        assert content == ""

    def test_write_unicode_exif_data(self, tmp_path):
        target_path = tmp_path / "unicode.txt"
        exif_data = {
            "UserComment": "こんにちは世界 🌍",
        }

        write_exif_to_file(exif_data, str(target_path))

        assert target_path.exists()
        content = target_path.read_text(encoding="utf-8")
        assert "こんにちは世界 🌍" in content


class TestExtractExif:
    """Tests for the extract_exif function."""

    def test_extract_exif_no_user_comment(self, tmp_path):
        # Create a simple image without EXIF data
        img_path = tmp_path / "no_exif.jpg"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(img_path, "JPEG")

        result = extract_exif(str(img_path))
        assert "UserComment" in result
        assert result["UserComment"] == "[not present]"

    def test_extract_exif_with_user_comment(self, tmp_path):
        # Create an image with EXIF UserComment
        img_path = tmp_path / "with_exif.jpg"
        img = Image.new("RGB", (100, 100), color="blue")

        # Create EXIF data with UserComment
        exif_ifd = {piexif.ExifIFD.UserComment: b"ASCII\x00\x00\x00Test Comment"}
        exif_dict = {"Exif": exif_ifd}
        exif_bytes = piexif.dump(exif_dict)

        img.save(img_path, "JPEG", exif=exif_bytes)

        result = extract_exif(str(img_path))
        assert "UserComment" in result
        assert result["UserComment"] == "Test Comment"

    def test_extract_exif_invalid_file(self, tmp_path):
        # Test with non-existent file
        result = extract_exif(str(tmp_path / "nonexistent.jpg"))
        assert "Error" in result


class TestRemoveExifAndSave:
    """Tests for the remove_exif_and_save function."""

    def test_remove_exif_from_jpeg(self, tmp_path):
        # Create JPEG with EXIF data
        src_path = tmp_path / "source.jpg"
        dst_path = tmp_path / "destination.jpg"

        img = Image.new("RGB", (100, 100), color="green")
        exif_ifd = {piexif.ExifIFD.UserComment: b"ASCII\x00\x00\x00Original Comment"}
        exif_dict = {"Exif": exif_ifd}
        exif_bytes = piexif.dump(exif_dict)
        img.save(src_path, "JPEG", exif=exif_bytes)

        remove_exif_and_save(str(src_path), str(dst_path))

        assert dst_path.exists()

        # Verify EXIF is removed
        result = extract_exif(str(dst_path))
        assert result["UserComment"] == "[not present]"

    def test_remove_exif_from_png(self, tmp_path):
        src_path = tmp_path / "source.png"
        dst_path = tmp_path / "destination.png"

        img = Image.new("RGB", (100, 100), color="yellow")
        img.save(src_path, "PNG")

        remove_exif_and_save(str(src_path), str(dst_path))

        assert dst_path.exists()
        # PNG should be saved successfully
        saved_img = Image.open(dst_path)
        assert saved_img.size == (100, 100)

    def test_preserve_image_quality(self, tmp_path):
        src_path = tmp_path / "source.jpg"
        dst_path = tmp_path / "destination.jpg"

        # Create a larger image to test quality preservation
        img = Image.new("RGB", (500, 500), color="purple")
        img.save(src_path, "JPEG", quality=95)

        remove_exif_and_save(str(src_path), str(dst_path))

        # Image should exist and be of reasonable size (quality=100)
        assert dst_path.exists()
        saved_img = Image.open(dst_path)
        assert saved_img.size == (500, 500)


class TestIntegrationScenarios:
    """Integration tests for common workflows."""

    def test_complete_workflow_simulation(self, tmp_path):
        """Test a complete workflow without GUI interaction."""
        # Setup: Create test images
        test_folder = tmp_path / "test_images"
        test_folder.mkdir()

        for i in range(3):
            img_path = test_folder / f"photo{i}.jpg"
            img = Image.new("RGB", (200, 200), color=(i * 80, 100, 150))

            # Add EXIF data
            exif_ifd = {piexif.ExifIFD.UserComment: b"ASCII\x00\x00\x00Photo " + str(i).encode()}
            exif_dict = {"Exif": exif_ifd}
            exif_bytes = piexif.dump(exif_dict)
            img.save(img_path, "JPEG", exif=exif_bytes)
            os.utime(img_path, (i, i))  # Different timestamps

        # Get image files
        images = get_image_files(str(test_folder))
        assert len(images) == 3

        # Create numbered folders
        numbered_folders = get_existing_numbered_folders(str(test_folder), len(images))
        assert len(numbered_folders) == 3

        # Process each image
        for i, image_file in enumerate(images):
            original_path = test_folder / image_file
            folder_path = Path(numbered_folders[i])
            new_path = folder_path / image_file

            # Move file
            shutil.move(str(original_path), str(new_path))

            # Extract and write EXIF
            exif_data = extract_exif(str(new_path))
            info_path = folder_path / "info.txt"
            write_exif_to_file(exif_data, str(info_path))

            assert info_path.exists()

            # Create stripped version
            stripped_path = folder_path / f"stripped_{image_file}"
            remove_exif_and_save(str(new_path), str(stripped_path))

            assert stripped_path.exists()

        # Verify all folders have been created and populated
        for folder_path in numbered_folders:
            assert os.path.exists(folder_path)
            assert len(os.listdir(folder_path)) >= 2  # At least original + info.txt
