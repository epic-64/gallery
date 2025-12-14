"""Preview panel module for displaying folder contents and image thumbnails."""

import logging
import os
import shutil
import subprocess
import sys
from tkinter import Button, Canvas, Frame, Label, Scrollbar, messagebox

from PIL import Image, ImageTk

logger = logging.getLogger(__name__)


class PreviewPanel:
    """Manages the preview panel for showing directory contents and thumbnails."""

    def __init__(self, parent):
        """Initialize the preview panel.

        Args:
            parent: The parent tkinter widget/frame where the preview will be displayed.
        """
        self.parent = parent
        self.preview_frame = None
        self.image_references = []  # Keep references to prevent garbage collection
        self.current_folder = None  # Track current folder for refresh
        self._create_panel()

    def _create_panel(self):
        """Create the preview panel UI structure."""
        preview_label = Label(
            self.parent, text="Folder Preview", font=("Segoe UI", 12, "bold"), bg="#f0f0f0", fg="#333333"
        )
        preview_label.pack(anchor="w", pady=(0, 10))

        # Create a frame with border for the preview area
        preview_container = Frame(self.parent, bg="#d0d0d0", relief="solid", bd=1)
        preview_container.pack(fill="both", expand=True)

        # Create canvas with scrollbar
        canvas = Canvas(preview_container, bg="#ffffff", highlightthickness=0)
        scrollbar = Scrollbar(preview_container, orient="vertical", command=canvas.yview)
        self.preview_frame = Frame(canvas, bg="#ffffff")

        self.preview_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=self.preview_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Bind mousewheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Initial message
        self._show_empty_message()

    def _show_empty_message(self):
        """Display the default empty state message."""
        empty_message = Label(
            self.preview_frame,
            text="No folder selected.\nUse 'Browse...' to select a folder.",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#999999",
            justify="center",
        )
        empty_message.pack(pady=50)

    def update(self, folder_path):
        """Update the preview panel with folder contents.

        Args:
            folder_path: Path to the folder to preview.
        """
        # Store current folder for refresh operations
        self.current_folder = folder_path

        # Clear previous content
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        self.image_references.clear()

        if not os.path.exists(folder_path):
            error_label = Label(
                self.preview_frame, text="Folder not found", font=("Segoe UI", 10), bg="#ffffff", fg="#cc0000"
            )
            error_label.pack(pady=50)
            return

        # Get all files and directories
        try:
            items = os.listdir(folder_path)
            items.sort()
        except PermissionError:
            error_label = Label(
                self.preview_frame, text="Permission denied", font=("Segoe UI", 10), bg="#ffffff", fg="#cc0000"
            )
            error_label.pack(pady=50)
            return

        if not items:
            empty_label = Label(
                self.preview_frame, text="Empty folder", font=("Segoe UI", 10), bg="#ffffff", fg="#999999"
            )
            empty_label.pack(pady=50)
            return

        # Supported image extensions
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

        # Separate directories and images
        directories = []
        images = []

        for item in items:
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                directories.append(item)
            else:
                _, ext = os.path.splitext(item.lower())
                if ext in image_extensions:
                    images.append(item)

        # Display directories
        if directories:
            self._display_directories(folder_path, directories)

        # Display images with thumbnails
        if images:
            self._display_images(folder_path, images)

        if not directories and not images:
            no_content_label = Label(
                self.preview_frame,
                text="No directories or images found",
                font=("Segoe UI", 10),
                bg="#ffffff",
                fg="#999999",
            )
            no_content_label.pack(pady=50)

    def _display_directories(self, folder_path, directories):
        """Display directory list in the preview.

        Args:
            folder_path: Base folder path.
            directories: List of directory names.
        """
        dir_header = Label(
            self.preview_frame,
            text=f"📁 Directories ({len(directories)})",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#333333",
            anchor="w",
        )
        dir_header.pack(fill="x", padx=10, pady=(10, 5))

        for directory in directories[:10]:  # Limit to first 10
            dir_frame = Frame(self.preview_frame, bg="#f8f8f8", relief="flat")
            dir_frame.pack(fill="x", padx=15, pady=2)

            dir_path = os.path.join(folder_path, directory)
            dir_label = Label(
                dir_frame,
                text=f"  📂 {directory}",
                font=("Segoe UI", 9),
                bg="#f8f8f8",
                fg="#0066cc",
                anchor="w",
                cursor="hand2",
            )
            dir_label.pack(fill="x", padx=5, pady=3)

            # Make clickable
            dir_label.bind("<Button-1>", lambda e, p=dir_path: self._open_in_explorer(p))
            dir_label.bind(
                "<Enter>", lambda e, lbl=dir_label: lbl.config(fg="#004499", font=("Segoe UI", 9, "underline"))
            )
            dir_label.bind("<Leave>", lambda e, lbl=dir_label: lbl.config(fg="#0066cc", font=("Segoe UI", 9)))

        if len(directories) > 10:
            more_label = Label(
                self.preview_frame,
                text=f"  ... and {len(directories) - 10} more",
                font=("Segoe UI", 8),
                bg="#ffffff",
                fg="#888888",
                anchor="w",
            )
            more_label.pack(fill="x", padx=15, pady=2)

    def _display_images(self, folder_path, images):
        """Display image list with thumbnails in the preview.

        Args:
            folder_path: Base folder path.
            images: List of image filenames.
        """
        img_header = Label(
            self.preview_frame,
            text=f"🖼️ Images ({len(images)})",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#333333",
            anchor="w",
        )
        img_header.pack(fill="x", padx=10, pady=(15, 5))

        # Show first 20 images with thumbnails
        for image_name in images[:20]:
            self._add_image_preview(folder_path, image_name)

        if len(images) > 20:
            more_label = Label(
                self.preview_frame,
                text=f"... and {len(images) - 20} more images",
                font=("Segoe UI", 8),
                bg="#ffffff",
                fg="#888888",
                anchor="w",
            )
            more_label.pack(fill="x", padx=15, pady=(5, 10))

    def _add_image_preview(self, folder_path, image_name):
        """Add a single image preview with thumbnail.

        Args:
            folder_path: Base folder path.
            image_name: Name of the image file.
        """
        image_path = os.path.join(folder_path, image_name)

        # Create frame for this image
        img_frame = Frame(self.preview_frame, bg="#fafafa", relief="solid", bd=1)
        img_frame.pack(fill="x", padx=15, pady=3)

        # Try to load thumbnail
        try:
            img = Image.open(image_path)

            # Get original dimensions
            orig_width, orig_height = img.size

            # Create thumbnail (max 80x80)
            img.thumbnail((80, 80), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            # Keep reference
            self.image_references.append(photo)

            # Thumbnail
            thumb_label = Label(img_frame, image=photo, bg="#fafafa", cursor="hand2")
            thumb_label.pack(side="left", padx=5, pady=5)

            # Make thumbnail clickable
            thumb_label.bind("<Button-1>", lambda e, p=image_path: self._open_image(p))

            # Image info
            info_frame = Frame(img_frame, bg="#fafafa")
            info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

            name_label = Label(
                info_frame,
                text=image_name,
                font=("Segoe UI", 9, "bold"),
                bg="#fafafa",
                fg="#0066cc",
                anchor="w",
                cursor="hand2",
            )
            name_label.pack(fill="x")

            # Make name clickable
            name_label.bind("<Button-1>", lambda e, p=image_path: self._open_image(p))
            name_label.bind(
                "<Enter>", lambda e, lbl=name_label: lbl.config(fg="#004499", font=("Segoe UI", 9, "bold underline"))
            )
            name_label.bind("<Leave>", lambda e, lbl=name_label: lbl.config(fg="#0066cc", font=("Segoe UI", 9, "bold")))

            size_label = Label(
                info_frame,
                text=f"{orig_width} × {orig_height} px",
                font=("Segoe UI", 8),
                bg="#fafafa",
                fg="#666666",
                anchor="w",
            )
            size_label.pack(fill="x")

            # File size
            file_size = os.path.getsize(image_path)
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"

            filesize_label = Label(
                info_frame, text=size_str, font=("Segoe UI", 8), bg="#fafafa", fg="#666666", anchor="w"
            )
            filesize_label.pack(fill="x")

            # Add Ignore button
            ignore_btn = Button(
                img_frame,
                text="Ignore",
                command=lambda: self._ignore_image(image_path, image_name),
                font=("Segoe UI", 8),
                bg="#ff6b6b",
                fg="white",
                activebackground="#ee5a52",
                activeforeground="white",
                cursor="hand2",
                relief="flat",
                padx=10,
                pady=3,
            )
            ignore_btn.pack(side="right", padx=5)

        except Exception:
            # If thumbnail fails, show text only
            error_label = Label(
                img_frame,
                text=f"❌ {image_name} (Could not load preview)",
                font=("Segoe UI", 9),
                bg="#fafafa",
                fg="#cc0000",
                anchor="w",
            )
            error_label.pack(fill="x", padx=10, pady=5)

    def _ignore_image(self, image_path, image_name):
        """Move an image to the 'ignore' subfolder.

        Args:
            image_path: Full path to the image file.
            image_name: Name of the image file.
        """
        try:
            # Get the folder containing the image
            folder_path = os.path.dirname(image_path)

            # Create ignore subfolder if it doesn't exist
            ignore_folder = os.path.join(folder_path, "ignore")
            os.makedirs(ignore_folder, exist_ok=True)

            # Destination path
            destination = os.path.join(ignore_folder, image_name)

            # Check if file already exists in ignore folder
            if os.path.exists(destination):
                response = messagebox.askyesno(
                    "File Exists", f"'{image_name}' already exists in the ignore folder.\nOverwrite it?"
                )
                if not response:
                    return

            # Move the image
            shutil.move(image_path, destination)
            logger.info(f"Moved {image_name} to ignore folder")

            # Refresh the preview
            if self.current_folder:
                self.update(self.current_folder)

        except Exception as e:
            logger.error(f"Failed to ignore image {image_name}: {e}")
            messagebox.showerror("Error", f"Could not move image to ignore folder:\n{e}")

    def _open_in_explorer(self, path):
        """Open a directory in the OS file explorer.

        Args:
            path: Path to the directory to open.
        """
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", path], check=True)
            else:  # linux
                subprocess.run(["xdg-open", path], check=True)
        except Exception as e:
            logger.error(f"Failed to open directory in explorer: {e}")
            messagebox.showerror("Error", f"Could not open directory:\n{e}")

    def _open_image(self, path):
        """Open an image file with the OS default image viewer.

        Args:
            path: Path to the image file to open.
        """
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", path], check=True)
            else:  # linux
                subprocess.run(["xdg-open", path], check=True)
        except Exception as e:
            logger.error(f"Failed to open image: {e}")
            messagebox.showerror("Error", f"Could not open image:\n{e}")
