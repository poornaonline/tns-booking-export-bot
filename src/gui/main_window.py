"""
Main GUI window for TNS Booking Uploader Bot.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
import threading
from pathlib import Path
from typing import Optional, Dict, Any

from ..utils.logger import get_logger
from ..utils.validators import Validator
from ..excel.processor import ExcelProcessor
from ..web.automation import WebAutomation

logger = get_logger()


class MainWindow:
    """Main application window using tkinter."""

    ICABBI_PORTAL_URL = "https://silvertopcorporate.business.icabbi.com/trips/all-trips"
    WINDOW_TITLE = "TNS Booking Uploader Bot"
    WINDOW_SIZE = "1400x700"  # Increased from 900x600

    def __init__(self):
        """Initialize the main window."""
        self.root = None
        self.selected_file_path = None
        self.excel_processor = None
        self.web_automation = None
        self.processed_data = None
        self.booking_statuses = {}  # Track status of each booking

        # Booking processing state
        self.bookings_to_process = []
        self.current_booking_index = 0
        self.total_bookings = 0
        self.is_processing = False  # Flag to track if processing is active
        self.stop_processing = False  # Flag to stop processing

        # GUI components
        self.file_path_var = None
        self.status_var = None
        self.progress_var = None
        self.bookings_tree = None
        self.clear_file_button = None

        self._setup_window()
        self._setup_components()
        self._configure_disabled_button_style()
    
    def _setup_window(self):
        """Set up the main window properties."""
        self.root = tk.Tk()
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry(self.WINDOW_SIZE)
        self.root.resizable(True, True)

        # Center the window on screen (increased width for Action column)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"1500x700+{x}+{y}")

        # Set minimum size
        self.root.minsize(1300, 600)

        # Configure grid weights for responsive design
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
    
    def _setup_components(self):
        """Set up all GUI components."""
        # Main frame with two columns
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_columnconfigure(0, weight=0)  # Left column (buttons)
        main_frame.grid_columnconfigure(1, weight=1)  # Right column (table)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left panel for controls
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 20))
        left_panel.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(
            left_panel,
            text="TNS Booking Uploader Bot",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 30))
        
        # Buttons frame
        buttons_frame = ttk.Frame(left_panel)
        buttons_frame.grid(row=2, column=0, pady=(0, 20), sticky=(tk.W, tk.E))
        buttons_frame.grid_columnconfigure(0, weight=1)

        # Open iCabbi Portal button
        self.portal_button = ttk.Button(
            buttons_frame,
            text="Open iCabbi Portal",
            command=self._open_portal,
            width=22
        )
        self.portal_button.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))

        # Select Booking File button
        self.upload_button = ttk.Button(
            buttons_frame,
            text="Select Booking File",
            command=self._start_upload,
            width=22
        )
        self.upload_button.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))

        # Start Processing Bookings button
        self.create_bookings_button = ttk.Button(
            buttons_frame,
            text="Start Processing Bookings",
            command=self._start_creating_bookings,
            width=22,
            state="disabled"  # Initially disabled
        )
        self.create_bookings_button.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))

        # Stop Processing button
        self.stop_button = ttk.Button(
            buttons_frame,
            text="Stop Processing",
            command=self._stop_processing,
            width=22,
            state="disabled"  # Initially disabled
        )
        self.stop_button.grid(row=3, column=0, pady=5, sticky=(tk.W, tk.E))

        # Clear File button
        self.clear_file_button = ttk.Button(
            buttons_frame,
            text="Clear File",
            command=self._clear_file,
            width=22,
            state="disabled"  # Initially disabled
        )
        self.clear_file_button.grid(row=4, column=0, pady=5, sticky=(tk.W, tk.E))

        # Clear Browser State button
        self.clear_state_button = ttk.Button(
            buttons_frame,
            text="Clear Browser State",
            command=self._clear_browser_state,
            width=22
        )
        self.clear_state_button.grid(row=5, column=0, pady=(10, 5), sticky=(tk.W, tk.E))

        # File selection frame
        file_frame = ttk.LabelFrame(left_panel, text="Selected File", padding="10")
        file_frame.grid(row=3, column=0, pady=(0, 15), sticky=(tk.W, tk.E))
        file_frame.grid_columnconfigure(0, weight=1)

        # File path display
        self.file_path_var = tk.StringVar(value="No file selected")
        file_path_label = ttk.Label(
            file_frame,
            textvariable=self.file_path_var,
            font=("Arial", 8),
            foreground="gray",
            wraplength=180
        )
        file_path_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Status frame
        status_frame = ttk.LabelFrame(left_panel, text="Status", padding="10")
        status_frame.grid(row=4, column=0, pady=(0, 15), sticky=(tk.W, tk.E))
        status_frame.grid_columnconfigure(0, weight=1)

        # Status display
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Arial", 8),
            wraplength=180
        )
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.grid(row=1, column=0, pady=(10, 0), sticky=(tk.W, tk.E))

        # Right panel for bookings table
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)

        # Table title
        table_title = ttk.Label(
            right_panel,
            text="Bookings",
            font=("Arial", 12, "bold")
        )
        table_title.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)

        # Create Treeview for bookings table
        table_frame = ttk.Frame(right_panel)
        table_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        # Treeview
        self.bookings_tree = ttk.Treeview(
            table_frame,
            columns=("date", "time", "driver", "mobile", "from", "to", "status", "action"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=20
        )

        vsb.config(command=self.bookings_tree.yview)
        hsb.config(command=self.bookings_tree.xview)

        # Define columns
        self.bookings_tree.heading("date", text="Date")
        self.bookings_tree.heading("time", text="Time")
        self.bookings_tree.heading("driver", text="Driver")
        self.bookings_tree.heading("mobile", text="Mobile")
        self.bookings_tree.heading("from", text="From")
        self.bookings_tree.heading("to", text="To")
        self.bookings_tree.heading("status", text="Status")
        self.bookings_tree.heading("action", text="Action")

        # Column widths - increased for better visibility
        self.bookings_tree.column("date", width=100, anchor=tk.CENTER)
        self.bookings_tree.column("time", width=80, anchor=tk.CENTER)
        self.bookings_tree.column("driver", width=150, anchor=tk.W)
        self.bookings_tree.column("mobile", width=120, anchor=tk.CENTER)
        self.bookings_tree.column("from", width=250, anchor=tk.W)
        self.bookings_tree.column("to", width=250, anchor=tk.W)
        self.bookings_tree.column("status", width=120, anchor=tk.CENTER)
        self.bookings_tree.column("action", width=100, anchor=tk.CENTER)

        # Grid layout
        self.bookings_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Configure tags for status colors
        self.bookings_tree.tag_configure("pending", foreground="gray")
        self.bookings_tree.tag_configure("processing", foreground="blue")
        self.bookings_tree.tag_configure("done", foreground="green")
        self.bookings_tree.tag_configure("error", foreground="red")

        # Bind click event to handle action column clicks
        self.bookings_tree.bind("<Button-1>", self._on_tree_click)
    
    def _configure_disabled_button_style(self):
        """Configure the style for disabled buttons to make them more visually obvious."""
        style = ttk.Style()

        # Map the disabled state to use lighter colors and different appearance
        style.map(
            "TButton",
            foreground=[("disabled", "gray50")],
            background=[("disabled", "gray85")],
            relief=[("disabled", "flat")]
        )

    def _open_portal(self):
        """Open the iCabbi portal in Chrome or Edge browser."""
        try:
            self._update_status("Opening iCabbi portal...")

            if not self.web_automation:
                from ..web.automation import WebAutomation
                self.web_automation = WebAutomation()

            success = self.web_automation.open_portal_in_browser()

            if success:
                self._update_status("iCabbi portal opened in browser")
            else:
                error_msg = ("Could not open portal. Please install Chrome or Microsoft Edge browser.\n\n"
                           "Chrome: https://www.google.com/chrome/\n"
                           "Edge: https://www.microsoft.com/edge/")
                self._update_status("Error: No preferred browser found")
                messagebox.showerror("Browser Required", error_msg)

        except Exception as e:
            error_msg = f"Failed to open iCabbi portal: {str(e)}"
            logger.error(error_msg)
            self._update_status("Error opening portal")
            messagebox.showerror("Error", error_msg)

    def _start_creating_bookings(self):
        """Handle Start Processing Bookings button click."""
        try:
            # Check if Excel file is loaded
            if not self.selected_file_path:
                messagebox.showwarning("No File Selected", "Please select a booking file first using 'Select Booking File'.")
                return

            logger.info(f"Starting booking creation with file: {self.selected_file_path}")
            logger.info(f"Number of bookings in processed_data: {len(self.processed_data) if self.processed_data else 0}")

            # Check if Excel data is processed
            if not hasattr(self, 'processed_data') or not self.processed_data:
                messagebox.showwarning("No Data", "Please wait for the file to be processed first.")
                return

            # Check if web automation is initialized (browser opened)
            if not self.web_automation or not hasattr(self.web_automation, 'page') or not self.web_automation.page:
                messagebox.showwarning("Browser Not Open",
                                     "Please open the iCabbi portal first by clicking 'Open iCabbi Portal'.")
                return

            self._update_status("Starting booking creation process...")

            # Disable start button, enable stop button
            self.create_bookings_button.config(state="disabled")
            self.stop_button.config(state="normal")

            # Get valid bookings
            valid_bookings = [row for row in self.processed_data if row.get('is_valid', False)]

            if not valid_bookings:
                self._on_booking_error("No valid bookings found")
                return

            # Filter out already processed bookings (status = 'done')
            bookings_to_process = []
            for idx, booking in enumerate(valid_bookings):
                # Check if this booking is already done
                is_done = False
                for item_id, info in self.booking_statuses.items():
                    if info['index'] == idx and info['status'] == 'done':
                        is_done = True
                        break

                if not is_done:
                    bookings_to_process.append((idx, booking))

            if not bookings_to_process:
                self._update_status("All bookings already processed!")
                self.create_bookings_button.config(state="normal")
                self.stop_button.config(state="disabled")
                messagebox.showinfo("Complete", "All bookings have already been processed!")
                return

            # Store bookings to process
            self.bookings_to_process = bookings_to_process
            self.current_booking_index = 0
            self.total_bookings = len(bookings_to_process)
            self.is_processing = True
            self.stop_processing = False

            # Disable all action buttons during batch processing
            self._disable_all_action_buttons()

            logger.info(f"Starting to process {self.total_bookings} bookings (skipping {len(valid_bookings) - self.total_bookings} already done)")

            # Start processing first booking (on main thread)
            self.root.after(100, self._process_next_booking)

        except Exception as e:
            error_msg = f"Error starting booking creation: {str(e)}"
            logger.error(error_msg)
            self._update_status("Error starting booking creation")
            messagebox.showerror("Error", error_msg)
            self.create_bookings_button.config(state="normal")

    def _process_next_booking(self):
        """Process the next booking in the queue (runs on main thread)."""
        try:
            # Check if stop was requested
            if self.stop_processing:
                self._on_processing_stopped()
                return

            # Check if we're done
            if self.current_booking_index >= self.total_bookings:
                self._on_all_bookings_complete(self.total_bookings)
                return

            # Get the actual booking index and data
            actual_index, booking = self.bookings_to_process[self.current_booking_index]

            # Update status to Processing
            self._update_booking_status(actual_index, 'processing')
            self._update_status(f"Processing booking {self.current_booking_index + 1} of {self.total_bookings}...")

            logger.info(f"Processing booking {self.current_booking_index + 1} of {self.total_bookings} (actual index: {actual_index})")

            # Process events to allow UI interaction (Stop button)
            self.root.update_idletasks()
            self.root.update()

            # Start the booking creation in chunks to keep UI responsive
            # We'll use a callback-based approach
            self._start_single_booking(actual_index, booking)

        except Exception as e:
            error_msg = f"Error processing booking {self.current_booking_index + 1}: {str(e)}"
            logger.error(error_msg)

            # Get actual index for error status
            if self.current_booking_index < len(self.bookings_to_process):
                actual_index, _ = self.bookings_to_process[self.current_booking_index]
                self._update_booking_status(actual_index, 'error')

            # Continue with next booking
            self.current_booking_index += 1
            self.root.after(500, self._process_next_booking)

    def _start_single_booking(self, actual_index, booking):
        """Start processing a single booking with periodic UI updates."""
        # Schedule the actual booking creation to run after a brief delay
        # This allows the UI to process the status update first
        self.root.after(100, self._execute_single_booking, actual_index, booking)

    def _execute_single_booking(self, actual_index, booking):
        """Execute the booking creation with periodic UI responsiveness checks."""
        try:
            # Set up a callback for the web automation to call periodically
            def ui_update_callback():
                """Called periodically during booking creation to keep UI responsive."""
                self.root.update_idletasks()
                self.root.update()
                return self.stop_processing  # Return True if stop was requested

            # Pass the callback to web automation
            self.web_automation.set_ui_callback(ui_update_callback)

            # Create the booking
            success = self.web_automation.create_single_booking(booking)

            # Clear the callback
            self.web_automation.set_ui_callback(None)

            # Update status based on result
            if success:
                self._update_booking_status(actual_index, 'done')
                logger.info(f"Booking {self.current_booking_index + 1} completed successfully")
            else:
                self._update_booking_status(actual_index, 'error')
                logger.error(f"Booking {self.current_booking_index + 1} failed")

            # Process events to keep UI responsive
            self.root.update_idletasks()
            self.root.update()

            # Update progress
            progress = ((self.current_booking_index + 1) / self.total_bookings) * 100
            self._update_progress(progress)

            # Move to next booking
            self.current_booking_index += 1

            # Schedule next booking (small delay to allow UI updates)
            self.root.after(500, self._process_next_booking)

        except Exception as e:
            error_msg = f"Error executing booking {self.current_booking_index + 1}: {str(e)}"
            logger.error(error_msg)
            self._update_booking_status(actual_index, 'error')

            # Continue with next booking
            self.current_booking_index += 1
            self.root.after(500, self._process_next_booking)

    def _stop_processing(self):
        """Handle Stop Processing button click."""
        if self.is_processing:
            self.stop_processing = True
            self._update_status("Stopping after current booking...")
            logger.info("User requested to stop processing")

    def _on_processing_stopped(self):
        """Handle when processing is stopped by user."""
        self.is_processing = False
        self.stop_processing = False
        self.create_bookings_button.config(state="normal")
        self.stop_button.config(state="disabled")

        # Re-enable all action buttons
        self._enable_all_action_buttons()

        # Count completed bookings
        completed = sum(1 for _, info in self.booking_statuses.items() if info['status'] == 'done')

        self._update_status(f"Processing stopped. {completed} bookings completed.")
        messagebox.showinfo("Stopped",
            f"Processing stopped by user.\n\n"
            f"{completed} bookings completed.\n"
            "You can resume by clicking 'Start Processing Bookings' again.\n"
            "Already completed bookings will be skipped.")

    def _on_all_bookings_complete(self, total_bookings: int):
        """Handle completion of all bookings."""
        self.is_processing = False
        self.stop_processing = False
        self._update_status(f"All {total_bookings} bookings processed!")
        self.create_bookings_button.config(state="normal")
        self.stop_button.config(state="disabled")

        # Re-enable all action buttons
        self._enable_all_action_buttons()

        # Count successes and failures
        done_count = sum(1 for _, info in self.booking_statuses.items() if info['status'] == 'done')
        error_count = sum(1 for _, info in self.booking_statuses.items() if info['status'] == 'error')

        messagebox.showinfo("Complete",
            f"All {total_bookings} bookings have been processed!\n\n"
            f"✓ Successfully created: {done_count}\n"
            f"✗ Failed: {error_count}\n\n"
            "Check the Status column for details.")

    def _on_booking_error(self, error_msg: str):
        """Handle booking processing error."""
        self.is_processing = False
        self.stop_processing = False
        self._update_status("Error processing bookings")
        self.create_bookings_button.config(state="normal")

        # Re-enable all action buttons
        self._enable_all_action_buttons()
        self.stop_button.config(state="disabled")
        messagebox.showerror("Booking Error", error_msg)

    def _clear_file(self):
        """Handle Clear File button click."""
        try:
            # Ask for confirmation
            result = messagebox.askyesno(
                "Clear File",
                "This will clear the loaded file and all booking data.\n\nAre you sure?"
            )

            if result:
                # Clear file path
                self.selected_file_path = None
                self.file_path_var.set("No file selected")

                # Clear processed data
                self.processed_data = None
                self.booking_statuses = {}

                # Reset processing state
                self.bookings_to_process = []
                self.current_booking_index = 0
                self.total_bookings = 0
                self.is_processing = False
                self.stop_processing = False

                # Clear table
                for item in self.bookings_tree.get_children():
                    self.bookings_tree.delete(item)

                # Disable buttons
                self.create_bookings_button.config(state="disabled")
                self.stop_button.config(state="disabled")
                self.clear_file_button.config(state="disabled")

                # Reset progress
                self._update_progress(0)
                self._update_status("File cleared. Ready to select a new file.")

                logger.info("File cleared successfully")

        except Exception as e:
            error_msg = f"Error clearing file: {str(e)}"
            logger.error(error_msg)
            self._update_status("Error clearing file")
            messagebox.showerror("Error", error_msg)

    def _clear_browser_state(self):
        """Handle Clear Browser State button click."""
        try:
            # Ask for confirmation with detailed message
            result = messagebox.askyesno(
                "Clear Browser State",
                "This will completely clear:\n\n"
                "• Saved login credentials\n"
                "• All cookies\n"
                "• All sessions\n"
                "• Browser cache\n\n"
                "You'll need to login again from scratch.\n\n"
                "Are you sure?"
            )

            if result:
                logger.info("User confirmed browser state clearing")

                if self.web_automation:
                    self.web_automation.clear_browser_state()
                else:
                    # Clear state file directly if automation not initialized
                    from ..web.automation import WebAutomation
                    temp_automation = WebAutomation()
                    temp_automation.clear_browser_state()

                self._update_status("Browser state cleared successfully")
                messagebox.showinfo(
                    "Success",
                    "Browser state cleared successfully!\n\n"
                    "✓ Login credentials removed\n"
                    "✓ Cookies deleted\n"
                    "✓ Sessions cleared\n"
                    "✓ Cache cleared\n\n"
                    "You'll need to login again next time you open the portal."
                )
                logger.info("Browser state cleared successfully")

        except Exception as e:
            error_msg = f"Error clearing browser state: {str(e)}"
            logger.error(error_msg)
            self._update_status("Error clearing browser state")
            messagebox.showerror("Error", f"Failed to clear browser state:\n\n{error_msg}")

    def _start_upload(self):
        """Start the booking upload process."""
        try:
            logger.info("Starting booking upload process")
            self._update_status("Selecting Excel file...")

            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select Excel File",
                filetypes=[
                    ("Excel files", "*.xlsx *.xls"),
                    ("All files", "*.*")
                ],
                initialdir=str(Path.home())
            )

            if not file_path:
                self._update_status("File selection cancelled")
                logger.info("File selection cancelled by user")
                return

            logger.info(f"User selected file: {file_path}")

            # Validate file
            if not Validator.is_valid_excel_file(file_path):
                error_msg = "Invalid Excel file selected"
                logger.error(error_msg)
                self._update_status("Invalid file selected")
                messagebox.showerror("Invalid File", error_msg)
                return

            # Update UI with selected file
            self.selected_file_path = file_path
            self.file_path_var.set(file_path)
            logger.info(f"File path stored in self.selected_file_path: {self.selected_file_path}")

            # Enable the Start Processing Bookings button
            self.create_bookings_button.config(state="normal")

            # Process file in background thread
            self._update_status("Processing Excel file...")
            logger.info(f"Starting background thread to process file: {file_path}")
            threading.Thread(
                target=self._process_excel_file,
                args=(file_path,),
                daemon=True
            ).start()

        except Exception as e:
            error_msg = f"Error starting upload process: {str(e)}"
            logger.error(error_msg)
            self._update_status("Error starting upload")
            messagebox.showerror("Error", error_msg)
    
    def _process_excel_file(self, file_path: str):
        """Process the selected Excel file (runs in background thread)."""
        try:
            logger.info(f"_process_excel_file called with file_path: {file_path}")

            # Initialize Excel processor if needed
            if not self.excel_processor:
                self.excel_processor = ExcelProcessor()

            # Process the file
            logger.info(f"Calling excel_processor.process_file with: {file_path}")
            result = self.excel_processor.process_file(file_path)

            # Update UI on main thread
            self.root.after(0, self._on_file_processed, result)

        except Exception as e:
            error_msg = f"Error processing Excel file '{file_path}': {str(e)}"
            logger.error(error_msg)
            self.root.after(0, self._on_processing_error, error_msg)
    
    def _on_file_processed(self, result):
        """Handle successful file processing (runs on main thread)."""
        try:
            if result.success:
                # Store processed data for booking creation
                self.processed_data = result.data

                # Clear existing table data
                for item in self.bookings_tree.get_children():
                    self.bookings_tree.delete(item)

                # Populate table with bookings
                self.booking_statuses = {}
                for idx, booking in enumerate(result.data):
                    # Format date and time for display
                    # Note: Excel processor returns capitalized keys (Date, Time, Driver, Mobile, From, To)
                    date_str = booking.get('Date', 'N/A')
                    if hasattr(date_str, 'strftime'):
                        date_str = date_str.strftime('%d/%m/%Y')

                    time_str = booking.get('Time', 'N/A')
                    if hasattr(time_str, 'strftime'):
                        time_str = time_str.strftime('%H:%M')

                    driver = booking.get('Driver', 'N/A')

                    # Get mobile number (optional field)
                    mobile = booking.get('Mobile', '')
                    if mobile and str(mobile).strip() and str(mobile).lower() != 'nan':
                        mobile_str = str(mobile).strip()
                    else:
                        mobile_str = ''

                    from_loc = booking.get('From', 'N/A')
                    to_loc = booking.get('To', 'N/A')

                    # Get existing status from Excel file
                    existing_status = booking.get('Status', '')

                    # Determine status and action button based on existing status
                    if existing_status and str(existing_status).strip().lower() == 'done':
                        status_display = "Done"
                        action_display = "✓ Done"
                        status_tag = "done"
                        internal_status = 'done'
                    else:
                        status_display = "Pending"
                        action_display = "▶ Process"
                        status_tag = "pending"
                        internal_status = 'pending'

                    # Insert into table with status from Excel file
                    item_id = self.bookings_tree.insert(
                        "",
                        tk.END,
                        values=(date_str, time_str, driver, mobile_str, from_loc, to_loc, status_display, action_display),
                        tags=(status_tag,)
                    )

                    # Track status by item ID
                    self.booking_statuses[item_id] = {
                        'index': idx,
                        'status': internal_status,
                        'booking': booking
                    }

                # Count already completed bookings
                already_done = sum(1 for info in self.booking_statuses.values() if info['status'] == 'done')

                status_msg = f"File processed successfully. {result.row_count} bookings loaded."
                if already_done > 0:
                    status_msg += f" ({already_done} already completed)"
                self._update_status(status_msg)
                self._update_progress(100)

                # Enable buttons
                self.create_bookings_button.config(state="normal")
                self.clear_file_button.config(state="normal")

                # Show success message
                success_msg = f"Excel file processed successfully!\n\n"
                success_msg += f"Bookings loaded: {result.row_count}\n"
                success_msg += f"Valid rows: {result.valid_rows}\n"
                success_msg += f"Invalid rows: {result.invalid_rows}"

                if already_done > 0:
                    success_msg += f"\n\n✓ Already completed: {already_done}\n"
                    success_msg += f"⏳ Pending: {result.row_count - already_done}"

                messagebox.showinfo("Success", success_msg)

            else:
                # Clear processed data on failure and disable button
                self.processed_data = None
                self.create_bookings_button.config(state="disabled")
                self.clear_file_button.config(state="disabled")
                error_msg = f"File processing failed: {result.error_message or 'Unknown error'}"
                self._update_status("File processing failed")
                messagebox.showerror("Processing Error", error_msg)
                logger.error(error_msg)

        except Exception as e:
            logger.error(f"Error handling file processing result: {str(e)}")
    
    def _on_processing_error(self, error_msg: str):
        """Handle file processing error (runs on main thread)."""
        self.create_bookings_button.config(state="disabled")
        self._update_status("File processing failed")
        messagebox.showerror("Processing Error", error_msg)
    
    def _update_status(self, message: str):
        """Update the status display."""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def _update_progress(self, value: float):
        """Update the progress bar."""
        self.progress_var.set(value)
        self.root.update_idletasks()

    def _update_booking_status(self, booking_index: int, status: str):
        """Update the status of a booking in the table and Excel file.

        Args:
            booking_index: Index of the booking in processed_data
            status: New status ('pending', 'processing', 'done', 'error')
        """
        try:
            # Find the tree item for this booking
            for item_id, info in self.booking_statuses.items():
                if info['index'] == booking_index:
                    # Update status in tracking dict
                    info['status'] = status

                    # Get current values
                    values = list(self.bookings_tree.item(item_id, 'values'))

                    # Update status column (second to last column)
                    status_text = {
                        'pending': 'Pending',
                        'processing': 'Processing...',
                        'done': 'Done',
                        'error': 'Error'
                    }.get(status, status)

                    values[-2] = status_text  # Status is second to last (action is last)

                    # Update action column based on status
                    if status == 'done':
                        values[-1] = "✓ Done"
                    elif status == 'error':
                        values[-1] = "⟳ Retry"
                    elif status == 'processing':
                        values[-1] = "⏸ Processing..."
                    else:  # pending
                        values[-1] = "▶ Process"

                    # Update tree item with new values and tag
                    self.bookings_tree.item(item_id, values=values, tags=(status,))

                    # Scroll to the item
                    self.bookings_tree.see(item_id)

                    # Update UI
                    self.root.update_idletasks()

                    # Update Excel file with status (only for done/error, not processing)
                    if status in ['done', 'error'] and self.selected_file_path:
                        booking = info['booking']
                        row_number = booking.get('row_number', booking_index + 2)
                        excel_status = 'Done' if status == 'done' else 'Error'

                        # Update Excel file in background thread to avoid blocking UI
                        threading.Thread(
                            target=self._update_excel_status,
                            args=(self.selected_file_path, row_number, excel_status),
                            daemon=True
                        ).start()

                    break

        except Exception as e:
            logger.error(f"Error updating booking status: {str(e)}")

    def _update_excel_status(self, file_path: str, row_number: int, status: str):
        """Update the status in the Excel file (runs in background thread)."""
        try:
            if self.excel_processor:
                self.excel_processor.update_booking_status(file_path, row_number, status)
        except Exception as e:
            logger.error(f"Error updating Excel status: {str(e)}")

    def _on_tree_click(self, event):
        """Handle clicks on the treeview to detect action button clicks."""
        try:
            # Identify the region clicked
            region = self.bookings_tree.identify_region(event.x, event.y)
            if region != "cell":
                return

            # Get the column clicked
            column = self.bookings_tree.identify_column(event.x)

            # Check if it's the action column (last column, #8)
            if column != "#8":
                return

            # Get the item clicked
            item_id = self.bookings_tree.identify_row(event.y)
            if not item_id:
                return

            # Check if we're already processing
            if self.is_processing:
                messagebox.showwarning(
                    "Processing in Progress",
                    "Another booking is currently being processed.\n\n"
                    "Please wait for it to complete or click 'Stop Processing'."
                )
                return

            # Get booking info
            booking_info = self.booking_statuses.get(item_id)
            if not booking_info:
                return

            status = booking_info['status']
            booking_index = booking_info['index']

            # Only allow processing if status is pending or error
            if status == 'processing':
                messagebox.showinfo(
                    "Already Processing",
                    "This booking is currently being processed."
                )
                return
            elif status == 'done':
                # Ask if user wants to reprocess
                result = messagebox.askyesno(
                    "Reprocess Booking",
                    "This booking has already been completed.\n\n"
                    "Do you want to process it again?"
                )
                if not result:
                    return

            # Start processing this single booking
            logger.info(f"User clicked to process booking at index {booking_index}")
            self._process_single_booking(booking_index, item_id)

        except Exception as e:
            logger.error(f"Error handling tree click: {str(e)}")

    def _process_single_booking(self, booking_index: int, item_id: str):
        """Process a single booking when user clicks the action button.

        Args:
            booking_index: Index of the booking in processed_data
            item_id: Tree item ID for UI updates
        """
        try:
            logger.info(f"Starting to process single booking at index {booking_index}")

            # Set processing flag
            self.is_processing = True
            self.stop_processing = False

            # Disable all action buttons during processing
            self._disable_all_action_buttons()

            # Disable main buttons
            self.create_bookings_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.clear_file_button.config(state="disabled")

            # Get the booking data
            booking = self.booking_statuses[item_id]['booking']

            # Update status to processing
            self._update_booking_status(booking_index, 'processing')
            self.root.update()

            # Update status message
            self._update_status(f"Processing booking {booking_index + 1}...")

            # Schedule the actual booking creation on main thread
            self.root.after(100, lambda: self._execute_single_booking_from_action(booking_index, booking, item_id))

        except Exception as e:
            logger.error(f"Error starting single booking processing: {str(e)}")
            self.is_processing = False
            self._enable_all_action_buttons()
            self.create_bookings_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.clear_file_button.config(state="normal")
            messagebox.showerror("Error", f"Failed to process booking:\n\n{str(e)}")

    def _execute_single_booking_from_action(self, booking_index: int, booking: Dict[str, Any], item_id: str):
        """Execute the booking creation for a single booking clicked by user."""
        try:
            # Set up a callback for the web automation to call periodically
            def ui_update_callback():
                """Called periodically during booking creation to keep UI responsive."""
                self.root.update_idletasks()
                self.root.update()
                return self.stop_processing  # Return True if stop was requested

            # Pass the callback to web automation
            self.web_automation.set_ui_callback(ui_update_callback)

            # Create the booking
            success = self.web_automation.create_single_booking(booking)

            # Clear the callback
            self.web_automation.set_ui_callback(None)

            # Update status based on result
            if success:
                self._update_booking_status(booking_index, 'done')
                self._update_status(f"Booking {booking_index + 1} completed successfully!")
                logger.info(f"Booking {booking_index + 1} completed successfully")
            else:
                self._update_booking_status(booking_index, 'error')
                self._update_status(f"Booking {booking_index + 1} failed!")
                logger.error(f"Booking {booking_index + 1} failed")

            # Force UI update
            self.root.update()

            # Re-enable buttons
            self.is_processing = False
            self._enable_all_action_buttons()
            self.create_bookings_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.clear_file_button.config(state="normal")

            # Update progress bar based on completed bookings
            self._update_progress_from_statuses()

        except Exception as e:
            if "stopped by user" in str(e).lower():
                logger.info(f"Booking {booking_index + 1} processing stopped by user")
                self._update_status(f"Processing stopped by user")
            else:
                logger.error(f"Error executing single booking: {str(e)}")
                self._update_booking_status(booking_index, 'error')
                self._update_status(f"Error processing booking {booking_index + 1}")

            # Re-enable buttons
            self.is_processing = False
            self._enable_all_action_buttons()
            self.create_bookings_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.clear_file_button.config(state="normal")

    def _disable_all_action_buttons(self):
        """Disable all action buttons in the table during processing."""
        for item_id in self.bookings_tree.get_children():
            values = list(self.bookings_tree.item(item_id, 'values'))
            values[-1] = "⏸ Disabled"
            self.bookings_tree.item(item_id, values=values)

    def _enable_all_action_buttons(self):
        """Re-enable all action buttons in the table after processing."""
        for item_id, info in self.booking_statuses.items():
            status = info['status']
            values = list(self.bookings_tree.item(item_id, 'values'))

            if status == 'done':
                values[-1] = "✓ Done"
            elif status == 'error':
                values[-1] = "⟳ Retry"
            elif status == 'processing':
                values[-1] = "⏸ Processing..."
            else:  # pending
                values[-1] = "▶ Process"

            self.bookings_tree.item(item_id, values=values)

    def _update_progress_from_statuses(self):
        """Update progress bar based on current booking statuses."""
        if not self.booking_statuses:
            return

        total = len(self.booking_statuses)
        completed = sum(1 for info in self.booking_statuses.values() if info['status'] == 'done')

        progress = (completed / total) * 100 if total > 0 else 0
        self._update_progress(progress)

    def run(self):
        """Start the GUI main loop."""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in GUI main loop: {str(e)}")
            raise
    
    def destroy(self):
        """Clean up and destroy the window."""
        try:
            if self.root:
                self.root.destroy()
                logger.info("Main window destroyed")
        except Exception as e:
            logger.error(f"Error destroying main window: {str(e)}")
