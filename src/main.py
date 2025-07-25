import logging
import os
from tkinter import Button, Entry, Frame, Label, Radiobutton, StringVar, Tk, filedialog, messagebox

try:
    from .preview import PreviewPanel
    from .process import process_images
    from .revert import revert_processing
except ImportError:
    from preview import PreviewPanel
    from process import process_images
    from revert import revert_processing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ImageProcessorApp:
    """Integrated image processing application with GUI."""

    def __init__(self, root):
        self.root = root
        self.root.title("Image Processing Tool")
        self.root.geometry("950x650")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")
        self.root.minsize(950, 650)

        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (950 // 2)
        y = (self.root.winfo_screenheight() // 2) - (650 // 2)
        self.root.geometry(f"950x650+{x}+{y}")

        # Variables
        self.folder_path = StringVar()
        self.base_name = StringVar()
        self.mode = StringVar(value="process")
        self.preview_panel = None  # Will be initialized in create_widgets

        self.create_widgets()

    def create_widgets(self):
        """Create all GUI widgets."""
        # Title
        title_label = Label(
            self.root, text="Image Processing Tool", font=("Segoe UI", 18, "bold"), bg="#f0f0f0", fg="#333333"
        )
        title_label.pack(pady=(15, 10))

        # Main container with two columns
        main_container = Frame(self.root, bg="#f0f0f0")
        main_container.pack(padx=20, pady=10, fill="both", expand=True)

        # Left side - Controls
        left_frame = Frame(main_container, bg="#f0f0f0")
        left_frame.pack(side="left", fill="both", padx=(0, 10))

        # Right side - Preview
        right_frame = Frame(main_container, bg="#f0f0f0")
        right_frame.pack(side="right", fill="both", expand=True)

        # Main content frame (left side)
        content_frame = Frame(left_frame, bg="#f0f0f0")
        content_frame.pack(padx=20, pady=0, fill="both", expand=True)

        # Folder selection section
        folder_frame = Frame(content_frame, bg="#f0f0f0")
        folder_frame.pack(fill="x", pady=(0, 20))

        folder_label = Label(
            folder_frame, text="Image Folder:", font=("Segoe UI", 10, "bold"), bg="#f0f0f0", fg="#333333"
        )
        folder_label.pack(anchor="w", pady=(0, 5))

        folder_input_frame = Frame(folder_frame, bg="#f0f0f0")
        folder_input_frame.pack(fill="x")

        self.folder_entry = Entry(
            folder_input_frame, textvariable=self.folder_path, font=("Segoe UI", 10), relief="solid", bd=1
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=5)

        browse_btn = Button(
            folder_input_frame,
            text="Browse...",
            command=self.browse_folder,
            font=("Segoe UI", 9),
            bg="#007ACC",
            fg="white",
            activebackground="#005A9E",
            activeforeground="white",
            cursor="hand2",
            relief="flat",
            padx=15,
        )
        browse_btn.pack(side="left", padx=(10, 0), ipady=3)

        # Mode selection section
        mode_frame = Frame(content_frame, bg="#f0f0f0")
        mode_frame.pack(fill="x", pady=(0, 20))

        mode_label = Label(
            mode_frame, text="Operation Mode:", font=("Segoe UI", 10, "bold"), bg="#f0f0f0", fg="#333333"
        )
        mode_label.pack(anchor="w", pady=(0, 8))

        # Radio buttons
        radio_frame = Frame(mode_frame, bg="#f0f0f0")
        radio_frame.pack(anchor="w", padx=10)

        process_radio = Radiobutton(
            radio_frame,
            text="Process Images",
            variable=self.mode,
            value="process",
            font=("Segoe UI", 10),
            bg="#f0f0f0",
            fg="#333333",
            selectcolor="#ffffff",
            activebackground="#f0f0f0",
            command=self.on_mode_change,
        )
        process_radio.pack(anchor="w", pady=2)

        process_desc = Label(
            radio_frame,
            text="Rename and organize images in the selected folder",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#666666",
        )
        process_desc.pack(anchor="w", padx=(25, 0), pady=(0, 8))

        revert_radio = Radiobutton(
            radio_frame,
            text="Revert Processing",
            variable=self.mode,
            value="revert",
            font=("Segoe UI", 10),
            bg="#f0f0f0",
            fg="#333333",
            selectcolor="#ffffff",
            activebackground="#f0f0f0",
            command=self.on_mode_change,
        )
        revert_radio.pack(anchor="w", pady=2)

        revert_desc = Label(
            radio_frame,
            text="Restore original filenames and folder structure",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#666666",
        )
        revert_desc.pack(anchor="w", padx=(25, 0))

        # Base name section
        self.name_frame = Frame(content_frame, bg="#f0f0f0")
        self.name_frame.pack(fill="x", pady=(0, 20))

        name_label = Label(
            self.name_frame, text="Base Filename:", font=("Segoe UI", 10, "bold"), bg="#f0f0f0", fg="#333333"
        )
        name_label.pack(anchor="w", pady=(0, 5))

        self.name_entry = Entry(
            self.name_frame, textvariable=self.base_name, font=("Segoe UI", 10), relief="solid", bd=1
        )
        self.name_entry.pack(fill="x", ipady=5)

        name_hint = Label(
            self.name_frame,
            text="Images will be renamed as: basename_001.jpg, basename_002.jpg, etc.",
            font=("Segoe UI", 8),
            bg="#f0f0f0",
            fg="#888888",
        )
        name_hint.pack(anchor="w", pady=(3, 0))

        # Preview Panel (right side)
        self.preview_panel = PreviewPanel(right_frame)

        # Action buttons
        button_frame = Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=(0, 20))

        run_btn = Button(
            button_frame,
            text="Run",
            command=self.run_operation,
            font=("Segoe UI", 11, "bold"),
            bg="#28a745",
            fg="white",
            activebackground="#218838",
            activeforeground="white",
            cursor="hand2",
            width=15,
            height=2,
            relief="flat",
        )
        run_btn.pack(side="left", padx=5)

        cancel_btn = Button(
            button_frame,
            text="Cancel",
            command=self.root.quit,
            font=("Segoe UI", 10),
            bg="#f0f0f0",
            fg="#666666",
            activebackground="#e0e0e0",
            activeforeground="#333333",
            cursor="hand2",
            width=15,
            height=2,
            relief="flat",
            bd=1,
        )
        cancel_btn.pack(side="left", padx=5)

    def browse_folder(self):
        """Open folder browser dialog."""
        folder_selected = filedialog.askdirectory(title="Select Image Folder")
        if folder_selected:
            self.folder_path.set(folder_selected)
            # Auto-fill base name with folder name if in process mode
            if self.mode.get() == "process":
                folder_name = os.path.basename(folder_selected.rstrip(os.sep))
                self.base_name.set(folder_name)
            # Update preview
            self.preview_panel.update(folder_selected)

    def on_mode_change(self):
        """Handle mode change to show/hide base name field."""
        if self.mode.get() == "revert":
            self.name_frame.pack_forget()
        else:
            self.name_frame.pack(fill="x", pady=(0, 20))

    def run_operation(self):
        """Execute the selected operation."""
        # Validate folder path
        folder = self.folder_path.get().strip()
        if not folder:
            messagebox.showerror("Error", "Please select an image folder.")
            return

        if not os.path.exists(folder):
            messagebox.showerror("Error", "The selected folder does not exist.")
            return

        logger.info(f"Selected folder: {folder}")

        mode = self.mode.get()

        if mode == "revert":
            self.run_revert(folder)
        else:
            self.run_process(folder)

    def run_revert(self, folder):
        """Run revert operation."""
        logger.info("Starting revert operation")
        restored_count, errors = revert_processing(folder)

        if errors:
            error_summary = "\n".join(errors[:5])
            if len(errors) > 5:
                error_summary += f"\n... and {len(errors) - 5} more error(s)"
            messagebox.showwarning(
                "Revert Completed with Errors", f"Restored {restored_count} image(s).\n\nErrors:\n{error_summary}"
            )
        else:
            messagebox.showinfo(
                "Revert Complete", f"Successfully restored {restored_count} image(s) and removed generated folders."
            )
        logger.info(f"Revert completed: {restored_count} files restored, {len(errors)} error(s)")

        # Refresh the preview to show updated folder contents
        self.preview_panel.update(folder)

    def run_process(self, folder):
        """Run image processing operation."""
        base_name = self.base_name.get().strip()
        if not base_name:
            messagebox.showerror("Error", "Please enter a base filename.")
            return

        logger.info(f"Starting image processing with base name: {base_name}")
        processed_count, errors = process_images(folder, base_name)

        if errors:
            error_summary = "\n".join(errors[:5])
            if len(errors) > 5:
                error_summary += f"\n... and {len(errors) - 5} more error(s)"
            messagebox.showwarning(
                "Processing Completed with Errors",
                f"Successfully processed {processed_count} image(s).\n\nErrors:\n{error_summary}",
            )
        else:
            messagebox.showinfo("Done", f"Successfully processed {processed_count} image(s).")
        logger.info(f"Processing completed: {processed_count} images processed, {len(errors)} error(s)")

        # Refresh the preview to show updated folder contents
        self.preview_panel.update(folder)


def main() -> None:
    """Main function to run the integrated application."""
    try:
        root = Tk()
        _ = ImageProcessorApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
