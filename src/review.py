"""Review mode module for going through images one by one."""

import logging
import os
import shutil
from tkinter import Button, Frame, Label, Toplevel, messagebox

from PIL import Image, ImageTk

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
        # Top info bar
        info_frame = Frame(self.window, bg="#2c3e50", height=60)
        info_frame.pack(fill="x")
        info_frame.pack_propagate(False)

        self.info_label = Label(
            info_frame,
            text="",
            font=("Segoe UI", 12, "bold"),
            bg="#2c3e50",
            fg="#ffffff",
        )
        self.info_label.pack(pady=15)

        # Image display area
        image_container = Frame(self.window, bg="#ffffff", relief="flat", bd=0)
        image_container.pack(fill="both", expand=True, padx=25, pady=25)

        # Image label
        self.image_label = Label(image_container, bg="#ffffff", text="Loading...", font=("Segoe UI", 14))
        self.image_label.pack(fill="both", expand=True, padx=20, pady=20)

        # Filename label below image
        self.filename_label = Label(
            image_container,
            text="",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
        )
        self.filename_label.pack(pady=(0, 10))

        # Button frame at the bottom
        button_frame = Frame(self.window, bg="#f5f7fa")
        button_frame.pack(pady=(0, 25))

        # Reject button
        reject_btn = Button(
            button_frame,
            text="❌ REJECT",
            command=self._reject_image,
            font=("Segoe UI", 14, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            cursor="hand2",
            width=15,
            height=2,
            relief="flat",
        )
        reject_btn.pack(side="left", padx=15)

        # Fix button
        fix_btn = Button(
            button_frame,
            text="🔧 FIX",
            command=self._fix_image,
            font=("Segoe UI", 14, "bold"),
            bg="#f39c12",
            fg="white",
            activebackground="#e67e22",
            activeforeground="white",
            cursor="hand2",
            width=15,
            height=2,
            relief="flat",
        )
        fix_btn.pack(side="left", padx=15)

        # Approve button
        approve_btn = Button(
            button_frame,
            text="✅ APPROVE",
            command=self._approve_image,
            font=("Segoe UI", 14, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            cursor="hand2",
            width=15,
            height=2,
            relief="flat",
        )
        approve_btn.pack(side="left", padx=15)

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
            fix_folder = os.path.join(self.folder_path, "_fix")
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
            ignore_folder = os.path.join(self.folder_path, "_ignore")
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
