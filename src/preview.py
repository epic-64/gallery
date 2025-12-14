"""Preview panel module for displaying folder contents and image thumbnails."""

import logging
import os
import shutil
import subprocess
import sys
from tkinter import Button, Canvas, Frame, Label, Scrollbar, messagebox

from PIL import Image, ImageTk

try:
    from .review import ReviewWindow
except ImportError:
    from review import ReviewWindow

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
        self.current_images = []  # Track current images for review mode
        self._create_panel()

    def _create_panel(self):
        """Create the preview panel UI structure."""
        # Header frame for title and refresh button
        header_frame = Frame(self.parent, bg="#ffffff")
        header_frame.pack(fill="x", pady=(0, 15), padx=25)

        preview_label = Label(
            header_frame, text="📂 Folder Preview", font=("Segoe UI", 13, "bold"), bg="#ffffff", fg="#2c3e50"
        )
        preview_label.pack(side="left", anchor="w")

        # Button container for right side
        button_container = Frame(header_frame, bg="#ffffff")
        button_container.pack(side="right", anchor="e")

        # Review button with modern styling
        self.review_btn = Button(
            button_container,
            text="👁️ Review",
            command=self._start_review,
            font=("Segoe UI", 9, "bold"),
            bg="#9b59b6",
            fg="white",
            activebackground="#8e44ad",
            activeforeground="white",
            cursor="hand2",
            relief="flat",
            padx=15,
            pady=5,
            state="disabled",  # Initially disabled until a folder is selected
        )
        self.review_btn.pack(side="right", padx=(0, 10))

        # Refresh button with modern styling
        self.refresh_btn = Button(
            button_container,
            text="🔄 Refresh",
            command=self._refresh_preview,
            font=("Segoe UI", 9, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            cursor="hand2",
            relief="flat",
            padx=15,
            pady=5,
            state="disabled",  # Initially disabled until a folder is selected
        )
        self.refresh_btn.pack(side="right")

        # Create a frame with border for the preview area
        preview_container = Frame(self.parent, bg="#ecf0f1", relief="flat", bd=0)
        preview_container.pack(fill="both", expand=True, padx=25, pady=(0, 25))

        # Create main container with two-column layout
        main_content = Frame(preview_container, bg="#fafbfc")
        main_content.pack(fill="both", expand=True)

        # Left column - Directories (with scrollbar) - narrower fixed width
        left_container = Frame(main_content, bg="#ecf0f1", relief="flat", bd=0, width=250)
        left_container.pack(side="left", fill="y", padx=(0, 5))
        left_container.pack_propagate(False)  # Prevent the frame from shrinking to fit its contents

        left_canvas = Canvas(left_container, bg="#fafbfc", highlightthickness=0)
        left_scrollbar = Scrollbar(left_container, orient="vertical", command=left_canvas.yview)
        self.dirs_frame = Frame(left_canvas, bg="#fafbfc")

        self.dirs_frame.bind("<Configure>", lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))

        left_canvas.create_window((0, 0), window=self.dirs_frame, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_scrollbar.pack(side="right", fill="y")
        left_canvas.pack(side="left", fill="both", expand=True)

        # Bind mousewheel to left canvas
        def on_left_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        left_canvas.bind("<Enter>", lambda e: left_canvas.bind("<MouseWheel>", on_left_mousewheel))
        left_canvas.bind("<Leave>", lambda e: left_canvas.unbind("<MouseWheel>"))
        self.dirs_frame.bind("<Enter>", lambda e: left_canvas.bind("<MouseWheel>", on_left_mousewheel))
        self.dirs_frame.bind("<Leave>", lambda e: left_canvas.unbind("<MouseWheel>"))

        # Right column - Images (with scrollbar)
        right_container = Frame(main_content, bg="#ecf0f1", relief="flat", bd=0)
        right_container.pack(side="right", fill="both", expand=True, padx=(5, 0))

        right_canvas = Canvas(right_container, bg="#fafbfc", highlightthickness=0)
        right_scrollbar = Scrollbar(right_container, orient="vertical", command=right_canvas.yview)
        self.images_frame = Frame(right_canvas, bg="#fafbfc")

        self.images_frame.bind("<Configure>", lambda e: right_canvas.configure(scrollregion=right_canvas.bbox("all")))

        right_canvas.create_window((0, 0), window=self.images_frame, anchor="nw")
        right_canvas.configure(yscrollcommand=right_scrollbar.set)

        right_scrollbar.pack(side="right", fill="y")
        right_canvas.pack(side="left", fill="both", expand=True)

        # Bind mousewheel to right canvas
        def on_right_mousewheel(event):
            right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        right_canvas.bind("<Enter>", lambda e: right_canvas.bind("<MouseWheel>", on_right_mousewheel))
        right_canvas.bind("<Leave>", lambda e: right_canvas.unbind("<MouseWheel>"))
        self.images_frame.bind("<Enter>", lambda e: right_canvas.bind("<MouseWheel>", on_right_mousewheel))
        self.images_frame.bind("<Leave>", lambda e: right_canvas.unbind("<MouseWheel>"))

        # Store canvas references for later use
        self.left_canvas = left_canvas
        self.right_canvas = right_canvas

        # Initial message (shown in the main preview_frame for now)
        self.preview_frame = main_content  # Keep reference for empty message
        self._show_empty_message()

    def _show_empty_message(self):
        """Display the default empty state message."""
        # Clear both frames
        for widget in self.dirs_frame.winfo_children():
            widget.destroy()
        for widget in self.images_frame.winfo_children():
            widget.destroy()

        # Show message in left frame
        empty_message_left = Label(
            self.dirs_frame,
            text="📁 Directories\n\nNo folder selected",
            font=("Segoe UI", 11),
            bg="#fafbfc",
            fg="#95a5a6",
            justify="center",
        )
        empty_message_left.pack(pady=80)

        # Show message in right frame
        empty_message_right = Label(
            self.images_frame,
            text="🖼️ Images\n\nNo folder selected",
            font=("Segoe UI", 11),
            bg="#fafbfc",
            fg="#95a5a6",
            justify="center",
        )
        empty_message_right.pack(pady=80)

    def _refresh_preview(self):
        """Refresh the current folder preview."""
        if self.current_folder:
            self.update(self.current_folder)

    def _start_review(self):
        """Start the review mode for all images in current folder."""
        if not self.current_folder or not self.current_images:
            messagebox.showinfo("No Images", "No images to review in the current folder.")
            return

        # Create a copy of the images list for the review window
        images_to_review = self.current_images.copy()

        # Open review window
        ReviewWindow(self.parent, self.current_folder, images_to_review)

        # Refresh preview after review window is closed (when it returns)
        self.update(self.current_folder)

    def update(self, folder_path):
        """Update the preview panel with folder contents.

        Args:
            folder_path: Path to the folder to preview.
        """
        # Store current folder for refresh operations
        self.current_folder = folder_path

        # Enable refresh button now that we have a folder
        self.refresh_btn.config(state="normal")

        # Clear previous content from both frames
        for widget in self.dirs_frame.winfo_children():
            widget.destroy()
        for widget in self.images_frame.winfo_children():
            widget.destroy()
        self.image_references.clear()

        if not os.path.exists(folder_path):
            error_label_left = Label(
                self.dirs_frame, text="❌ Folder not found", font=("Segoe UI", 11), bg="#fafbfc", fg="#e74c3c"
            )
            error_label_left.pack(pady=50)
            error_label_right = Label(
                self.images_frame, text="❌ Folder not found", font=("Segoe UI", 11), bg="#fafbfc", fg="#e74c3c"
            )
            error_label_right.pack(pady=50)
            return

        # Get all files and directories
        try:
            items = os.listdir(folder_path)
            items.sort()
        except PermissionError:
            error_label_left = Label(
                self.dirs_frame, text="🔒 Permission denied", font=("Segoe UI", 11), bg="#fafbfc", fg="#e74c3c"
            )
            error_label_left.pack(pady=50)
            error_label_right = Label(
                self.images_frame, text="🔒 Permission denied", font=("Segoe UI", 11), bg="#fafbfc", fg="#e74c3c"
            )
            error_label_right.pack(pady=50)
            return

        if not items:
            empty_label_left = Label(
                self.dirs_frame, text="📭 Empty folder", font=("Segoe UI", 11), bg="#fafbfc", fg="#95a5a6"
            )
            empty_label_left.pack(pady=50)
            empty_label_right = Label(
                self.images_frame, text="📭 Empty folder", font=("Segoe UI", 11), bg="#fafbfc", fg="#95a5a6"
            )
            empty_label_right.pack(pady=50)
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

        # Sort directories with custom logic
        directories = self._sort_directories(directories)

        # Sort images by creation date (oldest first)
        images = self._sort_images_by_creation_date(folder_path, images)

        # Store images for review mode
        self.current_images = images.copy()

        # Enable/disable review button based on whether we have images
        if images:
            self.review_btn.config(state="normal")
        else:
            self.review_btn.config(state="disabled")

        # Display directories in left frame
        if directories:
            self._display_directories(folder_path, directories)
        else:
            no_dirs_label = Label(
                self.dirs_frame,
                text="📂 No directories found",
                font=("Segoe UI", 11),
                bg="#fafbfc",
                fg="#95a5a6",
            )
            no_dirs_label.pack(pady=50)

        # Display images in right frame
        if images:
            self._display_images(folder_path, images)
        else:
            no_images_label = Label(
                self.images_frame,
                text="🖼️ No images found",
                font=("Segoe UI", 11),
                bg="#fafbfc",
                fg="#95a5a6",
            )
            no_images_label.pack(pady=50)

    def _sort_directories(self, directories):
        """Sort directories with custom logic:
        1. Directories with underscores come first (alphabetically among themselves)
        2. Numeric-only directories sorted by numeric value
        3. Other directories sorted alphabetically

        Args:
            directories: List of directory names to sort.

        Returns:
            Sorted list of directory names.
        """

        def sort_key(dirname):
            # Check if directory contains underscore
            has_underscore = "_" in dirname

            # Check if directory is numeric only
            is_numeric = dirname.isdigit()

            if has_underscore:
                # Priority 0: underscore directories, sorted alphabetically
                return (0, 0, dirname.lower())
            elif is_numeric:
                # Priority 1: numeric directories, sorted by numeric value
                return (1, int(dirname), "")
            else:
                # Priority 2: other directories, sorted alphabetically
                return (2, 0, dirname.lower())

        return sorted(directories, key=sort_key)

    def _sort_images_by_creation_date(self, folder_path, images):
        """Sort images by creation date (oldest first).

        Args:
            folder_path: Base folder path.
            images: List of image filenames to sort.

        Returns:
            Sorted list of image filenames.
        """

        def get_creation_time(filename):
            try:
                file_path = os.path.join(folder_path, filename)
                # Use birth time (creation time) on Windows, or fallback to modification time
                stat = os.stat(file_path)
                # st_birthtime is available on Windows and some Unix systems
                return getattr(stat, "st_birthtime", stat.st_mtime)
            except Exception:
                # Fallback to 0 if we can't get the time
                return 0

        return sorted(images, key=get_creation_time)

    def _display_directories(self, folder_path, directories):
        """Display directory list in the preview.

        Args:
            folder_path: Base folder path.
            directories: List of directory names.
        """
        dir_header = Label(
            self.dirs_frame,
            text=f"📁 Directories ({len(directories)})",
            font=("Segoe UI", 11, "bold"),
            bg="#fafbfc",
            fg="#2c3e50",
            anchor="w",
        )
        dir_header.pack(fill="x", padx=15, pady=(15, 8))

        # Display all directories (no limit, since they have their own scrollbar)
        for directory in directories:
            dir_frame = Frame(
                self.dirs_frame,
                bg="#ffffff",
                relief="solid",
                bd=1,
                highlightbackground="#e1e8ed",
                highlightthickness=1,
            )
            dir_frame.pack(fill="x", padx=20, pady=3)

            dir_path = os.path.join(folder_path, directory)
            dir_label = Label(
                dir_frame,
                text=f"  📂 {directory}",
                font=("Segoe UI", 10),
                bg="#ffffff",
                fg="#3498db",
                anchor="w",
                cursor="hand2",
            )
            dir_label.pack(fill="x", padx=10, pady=8)

            # Make clickable
            dir_label.bind("<Button-1>", lambda e, p=dir_path: self._open_in_explorer(p))
            dir_label.bind(
                "<Enter>", lambda e, lbl=dir_label: lbl.config(fg="#2980b9", font=("Segoe UI", 10, "underline"))
            )
            dir_label.bind("<Leave>", lambda e, lbl=dir_label: lbl.config(fg="#3498db", font=("Segoe UI", 10)))

    def _display_images(self, folder_path, images):
        """Display image list with thumbnails in the preview.

        Args:
            folder_path: Base folder path.
            images: List of image filenames.
        """
        img_header = Label(
            self.images_frame,
            text=f"🖼️ Images ({len(images)})",
            font=("Segoe UI", 11, "bold"),
            bg="#fafbfc",
            fg="#2c3e50",
            anchor="w",
        )
        img_header.pack(fill="x", padx=15, pady=(15, 8))

        # Show first 20 images with thumbnails
        for image_name in images[:20]:
            self._add_image_preview(folder_path, image_name)

        if len(images) > 20:
            more_label = Label(
                self.images_frame,
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

        # Create frame for this image with modern card styling
        img_frame = Frame(
            self.images_frame, bg="#ffffff", relief="solid", bd=1, highlightbackground="#e1e8ed", highlightthickness=1
        )
        img_frame.pack(fill="x", padx=20, pady=4)

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
            thumb_label = Label(img_frame, image=photo, bg="#ffffff", cursor="hand2")
            thumb_label.pack(side="left", padx=8, pady=8)

            # Make thumbnail clickable
            thumb_label.bind("<Button-1>", lambda e, p=image_path: self._open_image(p))

            # Image info
            info_frame = Frame(img_frame, bg="#ffffff")
            info_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)

            name_label = Label(
                info_frame,
                text=image_name,
                font=("Segoe UI", 10, "bold"),
                bg="#ffffff",
                fg="#2c3e50",
                anchor="w",
                cursor="hand2",
            )
            name_label.pack(fill="x")

            # Make name clickable
            name_label.bind("<Button-1>", lambda e, p=image_path: self._open_image(p))
            name_label.bind(
                "<Enter>", lambda e, lbl=name_label: lbl.config(fg="#3498db", font=("Segoe UI", 10, "bold underline"))
            )
            name_label.bind(
                "<Leave>", lambda e, lbl=name_label: lbl.config(fg="#2c3e50", font=("Segoe UI", 10, "bold"))
            )

            size_label = Label(
                info_frame,
                text=f"📐 {orig_width} × {orig_height} px",
                font=("Segoe UI", 9),
                bg="#ffffff",
                fg="#7f8c8d",
                anchor="w",
            )
            size_label.pack(fill="x", pady=(2, 0))

            # File size
            file_size = os.path.getsize(image_path)
            if file_size < 1024:
                size_str = f"💾 {file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"💾 {file_size / 1024:.1f} KB"
            else:
                size_str = f"💾 {file_size / (1024 * 1024):.1f} MB"

            filesize_label = Label(
                info_frame, text=size_str, font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", anchor="w"
            )
            filesize_label.pack(fill="x", pady=(2, 0))

            # Add Ignore button with modern styling
            ignore_btn = Button(
                img_frame,
                text="🚫 Ignore",
                command=lambda: self._ignore_image(image_path, image_name),
                font=("Segoe UI", 9, "bold"),
                bg="#e74c3c",
                fg="white",
                activebackground="#c0392b",
                activeforeground="white",
                cursor="hand2",
                relief="flat",
                padx=12,
                pady=6,
            )
            ignore_btn.pack(side="right", padx=8, pady=8)

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
            ignore_folder = os.path.join(folder_path, "_ignore")
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
