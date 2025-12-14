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
        self.preview_panel = None  # Will be initialized in create_widgets

        self.create_widgets()

    def create_widgets(self):
        """Create all GUI widgets."""
        # Header with gradient-like effect
        header_frame = Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        title_label = Label(
            header_frame, text="🖼️ Image Processing Tool", font=("Segoe UI", 22, "bold"), bg="#2c3e50", fg="#ffffff"
        )
        title_label.pack(pady=20)

        subtitle_label = Label(
            header_frame,
            text="Professional batch image renaming and organization",
            font=("Segoe UI", 9),
            bg="#2c3e50",
            fg="#bdc3c7",
        )
        subtitle_label.place(relx=0.5, rely=0.7, anchor="center")

        # Main container with two columns
        main_container = Frame(self.root, bg="#f5f7fa")
        main_container.pack(padx=25, pady=20, fill="both", expand=True)

        # Left side - Controls (Card style)
        left_frame = Frame(main_container, bg="#ffffff", relief="flat", bd=0)
        left_frame.pack(side="left", fill="both", padx=(0, 15))

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

        name_hint = Label(
            self.name_frame,
            text="💡 Images will be renamed as: basename_001.jpg, basename_002.jpg, etc.",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#7f8c8d",
        )
        name_hint.pack(anchor="w", pady=(8, 0))

        # Preview Panel (right side)
        self.preview_panel = PreviewPanel(right_frame)

        # Action buttons
        button_frame = Frame(self.root, bg="#f5f7fa")
        button_frame.pack(pady=(10, 25))

        run_btn = Button(
            button_frame,
            text="▶️  RUN OPERATION",
            command=self.run_operation,
            font=("Segoe UI", 12, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            cursor="hand2",
            width=20,
            height=2,
            relief="flat",
        )
        run_btn.pack(side="left", padx=8)

        cancel_btn = Button(
            button_frame,
            text="✖  CANCEL",
            command=self.root.quit,
            font=("Segoe UI", 11),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            cursor="hand2",
            width=15,
            height=2,
            relief="flat",
        )
        cancel_btn.pack(side="left", padx=8)

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
