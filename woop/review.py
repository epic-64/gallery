"""Review mode module for going through images one by one."""

import logging
import os
import shutil
from tkinter import Button, Frame, Label, Toplevel, messagebox

from PIL import Image, ImageTk

from .constants import FIX_FOLDER_NAME, IGNORE_FOLDER_NAME

logger = logging.getLogger(__name__)


class ReviewWindow:
    """Window for reviewing images one by one with approve/fix/reject options."""

    def __init__(self, parent, folder_path, images):
        """Initialize the review window.

        Args:
            parent: Parent tkinter widget.
            folder_path: Path to the folder containing images.
            images: List of image filenames to review (already sorted).
        """
        self.parent = parent
        self.folder_path = folder_path
        self.images = images
        self.current_index = 0
        self.photo = None  # Keep reference to prevent garbage collection

        # Create the window
        self.window = Toplevel(parent)
        self.window.title("Review Images")
        self.window.geometry("1200x800")
        self.window.configure(bg="#f5f7fa")

        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.window.winfo_screenheight() // 2) - (800 // 2)
        self.window.geometry(f"1200x800+{x}+{y}")

        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()

        self._create_widgets()
        self._load_current_image()

    def _create_widgets(self):
        """Create the UI widgets for review mode."""
        # Main container with two columns
        main_container = Frame(self.window, bg="#f5f7fa")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Left side - Image display area
        image_container = Frame(main_container, bg="#ffffff", relief="flat", bd=0)
        image_container.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Image label
        self.image_label = Label(image_container, bg="#ffffff", text="Loading...", font=("Segoe UI", 14))
        self.image_label.pack(fill="both", expand=True, padx=20, pady=20)

        # Right side - Controls panel (fixed width)
        controls_container = Frame(main_container, bg="#ffffff", relief="flat", bd=0, width=280)
        controls_container.pack(side="right", fill="y")
        controls_container.pack_propagate(False)

        # Info section at the top
        info_section = Frame(controls_container, bg="#ffffff")
        info_section.pack(fill="x", padx=20, pady=(20, 0))

        self.info_label = Label(
            info_section,
            text="",
            font=("Segoe UI", 13, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
            anchor="w",
        )
        self.info_label.pack(fill="x")

        # Filename label
        self.filename_label = Label(
            info_section,
            text="",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#7f8c8d",
            anchor="w",
            wraplength=240,
            justify="left",
        )
        self.filename_label.pack(fill="x", pady=(10, 0))

        # Spacer
        spacer = Frame(controls_container, bg="#ffffff", height=30)
        spacer.pack()

        # Buttons section
        buttons_section = Frame(controls_container, bg="#ffffff")
        buttons_section.pack(fill="x", padx=20, pady=10)

        # Approve button
        approve_btn = Button(
            buttons_section,
            text="✅ APPROVE",
            command=self._approve_image,
            font=("Segoe UI", 12, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            cursor="hand2",
            relief="flat",
            pady=15,
        )
        approve_btn.pack(fill="x", pady=(0, 10))

        # Fix button
        fix_btn = Button(
            buttons_section,
            text="🔧 FIX",
            command=self._fix_image,
            font=("Segoe UI", 12, "bold"),
            bg="#f39c12",
            fg="white",
            activebackground="#e67e22",
            activeforeground="white",
            cursor="hand2",
            relief="flat",
            pady=15,
        )
        fix_btn.pack(fill="x", pady=(0, 10))

        # Reject button
        reject_btn = Button(
            buttons_section,
            text="❌ REJECT",
            command=self._reject_image,
            font=("Segoe UI", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            cursor="hand2",
            relief="flat",
            pady=15,
        )
        reject_btn.pack(fill="x")

        # Keyboard shortcuts hint at the bottom
        hint_label = Label(
            controls_container,
            text="Keyboard shortcuts:\n→ Approve  |  ↓ Fix  |  ← Reject\nEsc to close",
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#95a5a6",
            justify="center",
        )
        hint_label.pack(side="bottom", pady=(20, 20))

        # Bind keyboard shortcuts
        self.window.bind("<Left>", lambda e: self._reject_image())
        self.window.bind("<Down>", lambda e: self._fix_image())
        self.window.bind("<Right>", lambda e: self._approve_image())
        self.window.bind("<Escape>", lambda e: self.window.destroy())

    def _load_current_image(self):
        """Load and display the current image."""
        if self.current_index >= len(self.images):
            # No more images
            self._show_completion()
            return

        image_name = self.images[self.current_index]
        image_path = os.path.join(self.folder_path, image_name)

        # Update info label
        self.info_label.config(text=f"Image {self.current_index + 1} of {len(self.images)}")

        # Update filename label
        self.filename_label.config(text=image_name)

        # Load and display image
        try:
            img = Image.open(image_path)

            # Get original dimensions
            orig_width, orig_height = img.size

            # Calculate size to fit in the display area (max 1100x600)
            max_width = 1100
            max_height = 600

            # Calculate scale to fit
            scale_width = max_width / orig_width
            scale_height = max_height / orig_height
            scale = min(scale_width, scale_height, 1.0)  # Don't upscale

            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)

            # Resize image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)

            # Update label
            self.image_label.config(image=self.photo, text="")

        except Exception as e:
            logger.error(f"Failed to load image {image_name}: {e}")
            self.image_label.config(
                image="",
                text=f"❌ Failed to load image:\n{image_name}\n\n{str(e)}",
                fg="#e74c3c",
            )
            self.photo = None

    def _approve_image(self):
        """Approve the current image and move to next."""
        logger.info(f"Approved: {self.images[self.current_index]}")
        self._next_image()

    def _fix_image(self):
        """Move current image to _fix folder and move to next."""
        image_name = self.images[self.current_index]
        image_path = os.path.join(self.folder_path, image_name)

        try:
            # Create _fix folder if it doesn't exist
            fix_folder = os.path.join(self.folder_path, FIX_FOLDER_NAME)
            os.makedirs(fix_folder, exist_ok=True)

            # Destination path
            destination = os.path.join(fix_folder, image_name)

            # Check if file already exists
            if os.path.exists(destination):
                response = messagebox.askyesno(
                    "File Exists",
                    f"'{image_name}' already exists in the _fix folder.\nOverwrite it?",
                    parent=self.window,
                )
                if not response:
                    return

            # Move the image
            shutil.move(image_path, destination)
            logger.info(f"Moved to _fix: {image_name}")

            # Remove from list
            self.images.pop(self.current_index)

            # Load next image (don't increment index since we removed current)
            self._load_current_image()

        except Exception as e:
            logger.error(f"Failed to move image to _fix: {e}")
            messagebox.showerror("Error", f"Could not move image to _fix folder:\n{e}", parent=self.window)

    def _reject_image(self):
        """Move current image to _ignore folder and move to next."""
        image_name = self.images[self.current_index]
        image_path = os.path.join(self.folder_path, image_name)

        try:
            # Create _ignore folder if it doesn't exist
            ignore_folder = os.path.join(self.folder_path, IGNORE_FOLDER_NAME)
            os.makedirs(ignore_folder, exist_ok=True)

            # Destination path
            destination = os.path.join(ignore_folder, image_name)

            # Check if file already exists
            if os.path.exists(destination):
                response = messagebox.askyesno(
                    "File Exists",
                    f"'{image_name}' already exists in the _ignore folder.\nOverwrite it?",
                    parent=self.window,
                )
                if not response:
                    return

            # Move the image
            shutil.move(image_path, destination)
            logger.info(f"Moved to _ignore: {image_name}")

            # Remove from list
            self.images.pop(self.current_index)

            # Load next image (don't increment index since we removed current)
            self._load_current_image()

        except Exception as e:
            logger.error(f"Failed to move image to _ignore: {e}")
            messagebox.showerror("Error", f"Could not move image to _ignore folder:\n{e}", parent=self.window)

    def _next_image(self):
        """Move to the next image."""
        self.current_index += 1
        self._load_current_image()

    def _show_completion(self):
        """Show completion message when all images are reviewed."""
        self.image_label.config(
            image="",
            text="🎉 All images reviewed!\n\nYou can close this window.",
            font=("Segoe UI", 16, "bold"),
            fg="#27ae60",
        )
        self.photo = None
        self.info_label.config(text="Review Complete")
        self.filename_label.config(text="")
