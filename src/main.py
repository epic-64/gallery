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
        self.root.geometry("1100x700")
        self.root.resizable(True, True)
        self.root.configure(bg="#f5f7fa")  # Modern light background
        self.root.minsize(1000, 650)

        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"1100x700+{x}+{y}")

        # Variables
        self.folder_path = StringVar()
        self.base_name = StringVar()
        self.mode = StringVar(value="process")
        self.number_mode = StringVar(value="prefix")  # "prefix" or "suffix"
        self.separator = StringVar(value=" #")
        self.preview_panel = None  # Will be initialized in create_widgets

        self.create_widgets()

    def create_widgets(self):
        """Create all GUI widgets."""

        # Main container with two columns
        main_container = Frame(self.root, bg="#f5f7fa")
        main_container.pack(padx=25, pady=20, fill="both", expand=True)

        # Left side - Controls (Card style) with fixed width
        left_frame = Frame(main_container, bg="#ffffff", relief="flat", bd=0, width=400)
        left_frame.pack(side="left", fill="y", padx=(0, 15))
        left_frame.pack_propagate(False)  # Prevent frame from resizing to fit contents

        # Add subtle shadow effect with a border frame
        left_border = Frame(main_container, bg="#e8ecef", relief="flat")
        left_border.place(in_=left_frame, relx=0, rely=0, relwidth=1, relheight=1)
        left_border.lower()

        # Right side - Preview (Card style)
        right_frame = Frame(main_container, bg="#ffffff", relief="flat", bd=0)
        right_frame.pack(side="right", fill="both", expand=True)

        # Add subtle shadow effect
        right_border = Frame(main_container, bg="#e8ecef", relief="flat")
        right_border.place(in_=right_frame, relx=0, rely=0, relwidth=1, relheight=1)
        right_border.lower()

        # Main content frame (left side) with padding
        content_frame = Frame(left_frame, bg="#ffffff")
        content_frame.pack(padx=25, pady=25, fill="both", expand=True)

        # Folder selection section
        folder_frame = Frame(content_frame, bg="#ffffff")
        folder_frame.pack(fill="x", pady=(0, 25))

        folder_label = Label(
            folder_frame, text="📁 Image Folder", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#2c3e50"
        )
        folder_label.pack(anchor="w", pady=(0, 8))

        folder_input_frame = Frame(folder_frame, bg="#ffffff")
        folder_input_frame.pack(fill="x")

        self.folder_entry = Entry(
            folder_input_frame,
            textvariable=self.folder_path,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            bg="#f8f9fa",
            fg="#2c3e50",
            insertbackground="#2c3e50",
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=8)

        browse_btn = Button(
            folder_input_frame,
            text="📂 Browse",
            command=self.browse_folder,
            font=("Segoe UI", 10, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            cursor="hand2",
            relief="flat",
            padx=20,
            pady=8,
        )
        browse_btn.pack(side="left", padx=(12, 0))

        # Mode selection section
        mode_frame = Frame(content_frame, bg="#ffffff")
        mode_frame.pack(fill="x", pady=(0, 25))

        mode_label = Label(
            mode_frame, text="⚙️ Operation Mode", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#2c3e50"
        )
        mode_label.pack(anchor="w", pady=(0, 12))

        # Radio buttons with card-style backgrounds
        radio_frame = Frame(mode_frame, bg="#ffffff")
        radio_frame.pack(anchor="w", fill="x")

        # Process option card
        process_card = Frame(
            radio_frame, bg="#e8f5e9", relief="solid", bd=1, highlightbackground="#27ae60", highlightthickness=1
        )
        process_card.pack(fill="x", pady=(0, 10))

        process_radio = Radiobutton(
            process_card,
            text="✨ Process Images",
            variable=self.mode,
            value="process",
            font=("Segoe UI", 11, "bold"),
            bg="#e8f5e9",
            fg="#27ae60",
            selectcolor="#e8f5e9",
            activebackground="#e8f5e9",
            command=self.on_mode_change,
        )
        process_radio.pack(anchor="w", padx=15, pady=(10, 5))

        process_desc = Label(
            process_card,
            text="Rename and organize images in the selected folder",
            font=("Segoe UI", 9),
            bg="#e8f5e9",
            fg="#27ae60",
        )
        process_desc.pack(anchor="w", padx=(40, 15), pady=(0, 10))

        # Revert option card
        revert_card = Frame(
            radio_frame, bg="#fff3e0", relief="solid", bd=1, highlightbackground="#f39c12", highlightthickness=1
        )
        revert_card.pack(fill="x")

        revert_radio = Radiobutton(
            revert_card,
            text="↩️ Revert Processing",
            variable=self.mode,
            value="revert",
            font=("Segoe UI", 11, "bold"),
            bg="#fff3e0",
            fg="#e67e22",
            selectcolor="#fff3e0",
            activebackground="#fff3e0",
            command=self.on_mode_change,
        )
        revert_radio.pack(anchor="w", padx=15, pady=(10, 5))

        revert_desc = Label(
            revert_card,
            text="Restore original filenames and folder structure",
            font=("Segoe UI", 9),
            bg="#fff3e0",
            fg="#e67e22",
        )
        revert_desc.pack(anchor="w", padx=(40, 15), pady=(0, 10))

        # Base name section
        self.name_frame = Frame(content_frame, bg="#ffffff")
        self.name_frame.pack(fill="x", pady=(0, 25))

        name_label = Label(
            self.name_frame, text="✏️ Base Filename", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#2c3e50"
        )
        name_label.pack(anchor="w", pady=(0, 8))

        self.name_entry = Entry(
            self.name_frame,
            textvariable=self.base_name,
            font=("Segoe UI", 11),
            relief="solid",
            bd=1,
            bg="#f8f9fa",
            fg="#2c3e50",
            insertbackground="#2c3e50",
        )
        self.name_entry.pack(fill="x", ipady=10)
        self.name_entry.bind("<KeyRelease>", lambda e: self._update_filename_preview())

        name_hint = Label(
            self.name_frame,
            text="💡 Example preview will be shown below",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#7f8c8d",
        )
        name_hint.pack(anchor="w", pady=(8, 0))

        # Number mode section
        self.number_mode_frame = Frame(content_frame, bg="#ffffff")
        self.number_mode_frame.pack(fill="x", pady=(0, 20))

        mode_label = Label(
            self.number_mode_frame,
            text="🔢 Number Position",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
        )
        mode_label.pack(anchor="w", pady=(0, 8))

        mode_options_frame = Frame(self.number_mode_frame, bg="#ffffff")
        mode_options_frame.pack(anchor="w", fill="x")

        prefix_radio = Radiobutton(
            mode_options_frame,
            text="Prefix (001 - basename)",
            variable=self.number_mode,
            value="prefix",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#2c3e50",
            selectcolor="#ffffff",
            activebackground="#ffffff",
            command=self._update_filename_preview,
        )
        prefix_radio.pack(anchor="w", pady=2)

        suffix_radio = Radiobutton(
            mode_options_frame,
            text="Suffix (basename - 001)",
            variable=self.number_mode,
            value="suffix",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#2c3e50",
            selectcolor="#ffffff",
            activebackground="#ffffff",
            command=self._update_filename_preview,
        )
        suffix_radio.pack(anchor="w", pady=2)

        # Separator section
        self.separator_frame = Frame(content_frame, bg="#ffffff")
        self.separator_frame.pack(fill="x", pady=(0, 20))

        separator_label = Label(
            self.separator_frame,
            text="➖ Separator",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
        )
        separator_label.pack(anchor="w", pady=(0, 8))

        self.separator_entry = Entry(
            self.separator_frame,
            textvariable=self.separator,
            font=("Segoe UI", 11),
            relief="solid",
            bd=1,
            bg="#f8f9fa",
            fg="#2c3e50",
            insertbackground="#2c3e50",
            width=10,
        )
        self.separator_entry.pack(anchor="w", ipady=8)
        self.separator_entry.bind("<KeyRelease>", lambda e: self._update_filename_preview())

        # Preview example
        self.preview_example_label = Label(
            self.separator_frame,
            text="",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#27ae60",
        )
        self.preview_example_label.pack(anchor="w", pady=(8, 0))

        # RUN button frame (always at the bottom of settings panel)
        self.button_frame = Frame(content_frame, bg="#ffffff")
        self.button_frame.pack(side="bottom", fill="x", pady=(15, 0))

        run_btn = Button(
            self.button_frame,
            text="▶️  RUN OPERATION",
            command=self.run_operation,
            font=("Segoe UI", 12, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            cursor="hand2",
            relief="flat",
            padx=20,
            pady=12,
        )
        run_btn.pack(fill="x")

        # Preview Panel (right side)
        self.preview_panel = PreviewPanel(right_frame)

    def browse_folder(self):
        """Open folder browser dialog."""
        folder_selected = filedialog.askdirectory(title="Select Image Folder")
        if folder_selected:
            self.folder_path.set(folder_selected)
            # Auto-fill base name with folder name if in process mode
            if self.mode.get() == "process":
                folder_name = os.path.basename(folder_selected.rstrip(os.sep))
                self.base_name.set(folder_name)
                self._update_filename_preview()
            # Update preview
            self.preview_panel.update(folder_selected)

    def on_mode_change(self):
        """Handle mode change to show/hide base name field."""
        if self.mode.get() == "revert":
            self.name_frame.pack_forget()
            self.number_mode_frame.pack_forget()
            self.separator_frame.pack_forget()
        else:
            self.name_frame.pack(fill="x", pady=(0, 25), before=self.button_frame)
            self.number_mode_frame.pack(fill="x", pady=(0, 20), before=self.button_frame)
            self.separator_frame.pack(fill="x", pady=(0, 20), before=self.button_frame)
            self._update_filename_preview()

    def _update_filename_preview(self):
        """Update the filename preview example."""
        base_name = self.base_name.get().strip()
        separator = self.separator.get()
        number_mode = self.number_mode.get()

        if not base_name:
            self.preview_example_label.config(text="")
            return

        # Generate example
        if number_mode == "prefix":
            example = f"📝 Example: 001{separator}{base_name}.jpg, 002{separator}{base_name}.jpg, ..."
        else:  # suffix
            example = f"📝 Example: {base_name}{separator}001.jpg, {base_name}{separator}002.jpg, ..."

        self.preview_example_label.config(text=example)

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

        number_mode = self.number_mode.get()
        separator = self.separator.get()

        logger.info(
            f"Starting image processing with base name: {base_name}, mode: {number_mode}, separator: '{separator}'"
        )
        processed_count, errors = process_images(folder, base_name, number_mode, separator)

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
