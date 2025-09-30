"""
Main GUI window for TNS Booking Uploader Bot.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
import threading
from pathlib import Path
from typing import Optional

from ..utils.logger import get_logger
from ..utils.validators import Validator
from ..excel.processor import ExcelProcessor
from ..web.automation import WebAutomation

logger = get_logger()


class MainWindow:
    """Main application window using tkinter."""

    ICABBI_PORTAL_URL = "https://silvertopcorporate.business.icabbi.com/trips/all-trips"
    WINDOW_TITLE = "TNS Booking Uploader Bot"
    WINDOW_SIZE = "900x600"

    def __init__(self):
        """Initialize the main window."""
        self.root = None
        self.selected_file_path = None
        self.excel_processor = None
        self.web_automation = None
        self.processed_data = None
        self.booking_statuses = {}  # Track status of each booking

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

        # Center the window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"900x600+{x}+{y}")

        # Set minimum size
        self.root.minsize(800, 500)

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
        title_label.grid(row=0, column=0, pady=(0, 10))

        # Description
        desc_label = ttk.Label(
            left_panel,
            text="Automate booking uploads\nto iCabbi portal",
            font=("Arial", 9),
            justify=tk.CENTER
        )
        desc_label.grid(row=1, column=0, pady=(0, 20))
        
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

        # Clear File button
        self.clear_file_button = ttk.Button(
            buttons_frame,
            text="Clear File",
            command=self._clear_file,
            width=22,
            state="disabled"  # Initially disabled
        )
        self.clear_file_button.grid(row=3, column=0, pady=5, sticky=(tk.W, tk.E))

        # Clear Browser State button
        self.clear_state_button = ttk.Button(
            buttons_frame,
            text="Clear Browser State",
            command=self._clear_browser_state,
            width=22
        )
        self.clear_state_button.grid(row=4, column=0, pady=(10, 5), sticky=(tk.W, tk.E))

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

        # Footer
        footer_label = ttk.Label(
            left_panel,
            text="© 2025 TNS\nInternal Use Only",
            font=("Arial", 7),
            foreground="gray",
            justify=tk.CENTER
        )
        footer_label.grid(row=5, column=0, pady=(20, 0))

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
            columns=("date", "time", "driver", "mobile", "from", "to", "status"),
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

        # Column widths
        self.bookings_tree.column("date", width=90, anchor=tk.CENTER)
        self.bookings_tree.column("time", width=70, anchor=tk.CENTER)
        self.bookings_tree.column("driver", width=100, anchor=tk.W)
        self.bookings_tree.column("mobile", width=100, anchor=tk.CENTER)
        self.bookings_tree.column("from", width=120, anchor=tk.W)
        self.bookings_tree.column("to", width=120, anchor=tk.W)
        self.bookings_tree.column("status", width=100, anchor=tk.CENTER)

        # Grid layout
        self.bookings_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Configure tags for status colors
        self.bookings_tree.tag_configure("pending", foreground="gray")
        self.bookings_tree.tag_configure("processing", foreground="blue")
        self.bookings_tree.tag_configure("done", foreground="green")
        self.bookings_tree.tag_configure("error", foreground="red")
    
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

            # Start the booking creation process
            success = self.web_automation.start_booking_creation(self.processed_data)

            if success:
                self._update_status("Booking created successfully!")
                messagebox.showinfo("Success",
                    "Booking created successfully!\n\n"
                    "The following steps were completed:\n"
                    "✓ Step 1: Driver name and mobile filled\n"
                    "✓ Step 2: Pickup and destination addresses filled\n"
                    "✓ Step 2: Date and time filled\n"
                    "✓ Step 3: Intermediate page navigated\n"
                    "✓ Step 4: Project Name filled (Metro)\n"
                    "✓ Step 5: 'Book now' button clicked\n\n"
                    "Check the browser for confirmation.")
            else:
                error_msg = "Failed to create booking. Check the browser and try again."
                self._update_status("Failed to create booking")
                messagebox.showerror("Booking Creation Error", error_msg)

        except Exception as e:
            error_msg = f"Error starting booking creation: {str(e)}"
            logger.error(error_msg)
            self._update_status("Error starting booking creation")
            messagebox.showerror("Error", error_msg)

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

                # Clear table
                for item in self.bookings_tree.get_children():
                    self.bookings_tree.delete(item)

                # Disable buttons
                self.create_bookings_button.config(state="disabled")
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
            # Ask for confirmation
            result = messagebox.askyesno(
                "Clear Browser State",
                "This will clear saved login information and you'll need to log in again.\n\nAre you sure?"
            )

            if result:
                if self.web_automation:
                    self.web_automation.clear_browser_state()
                else:
                    # Clear state file directly if automation not initialized
                    from ..web.automation import WebAutomation
                    temp_automation = WebAutomation()
                    temp_automation.clear_browser_state()

                self._update_status("Browser state cleared")
                messagebox.showinfo("Success", "Browser state cleared successfully. You'll need to log in again next time.")

        except Exception as e:
            error_msg = f"Error clearing browser state: {str(e)}"
            logger.error(error_msg)
            self._update_status("Error clearing browser state")
            messagebox.showerror("Error", error_msg)

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

                    # Insert into table with "Pending" status
                    item_id = self.bookings_tree.insert(
                        "",
                        tk.END,
                        values=(date_str, time_str, driver, mobile_str, from_loc, to_loc, "Pending"),
                        tags=("pending",)
                    )

                    # Track status by item ID
                    self.booking_statuses[item_id] = {
                        'index': idx,
                        'status': 'pending'
                    }

                status_msg = f"File processed successfully. {result.row_count} bookings loaded."
                self._update_status(status_msg)
                self._update_progress(100)

                # Enable buttons
                self.create_bookings_button.config(state="normal")
                self.clear_file_button.config(state="normal")

                # Show success message
                messagebox.showinfo(
                    "Success",
                    f"Excel file processed successfully!\n\n"
                    f"Bookings loaded: {result.row_count}\n"
                    f"Valid rows: {result.valid_rows}\n"
                    f"Invalid rows: {result.invalid_rows}"
                )

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
        """Update the status of a booking in the table.

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

                    # Update status column (last column)
                    status_text = {
                        'pending': 'Pending',
                        'processing': 'Processing...',
                        'done': 'Done',
                        'error': 'Error'
                    }.get(status, status)

                    values[-1] = status_text

                    # Update tree item with new values and tag
                    self.bookings_tree.item(item_id, values=values, tags=(status,))

                    # Scroll to the item
                    self.bookings_tree.see(item_id)

                    # Update UI
                    self.root.update_idletasks()
                    break

        except Exception as e:
            logger.error(f"Error updating booking status: {str(e)}")
    
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
