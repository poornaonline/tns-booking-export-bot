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
    WINDOW_SIZE = "450x400"
    
    def __init__(self):
        """Initialize the main window."""
        self.root = None
        self.selected_file_path = None
        self.excel_processor = None
        self.web_automation = None
        self.processed_data = None
        
        # GUI components
        self.file_path_var = None
        self.status_var = None
        self.progress_var = None
        
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
        x = (self.root.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"450x400+{x}+{y}")

        # Set minimum size
        self.root.minsize(400, 350)
        
        # Configure grid weights for responsive design
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
    
    def _setup_components(self):
        """Set up all GUI components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="TNS Booking Uploader Bot",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Automate booking data uploads to iCabbi portal",
            font=("Arial", 10)
        )
        desc_label.grid(row=1, column=0, pady=(0, 30))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, pady=(0, 20), sticky=(tk.W, tk.E))
        buttons_frame.grid_columnconfigure(0, weight=1)

        # Open iCabbi Portal button
        self.portal_button = ttk.Button(
            buttons_frame,
            text="Open iCabbi Portal",
            command=self._open_portal,
            width=25
        )
        self.portal_button.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))

        # Select Booking File button
        self.upload_button = ttk.Button(
            buttons_frame,
            text="Select Booking File",
            command=self._start_upload,
            width=25
        )
        self.upload_button.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))

        # Start Processing Bookings button
        self.create_bookings_button = ttk.Button(
            buttons_frame,
            text="Start Processing Bookings",
            command=self._start_creating_bookings,
            width=25,
            state="disabled"  # Initially disabled
        )
        self.create_bookings_button.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))

        # Clear Browser State button (smaller, for troubleshooting)
        self.clear_state_button = ttk.Button(
            buttons_frame,
            text="Clear Browser State",
            command=self._clear_browser_state,
            width=25
        )
        self.clear_state_button.grid(row=3, column=0, pady=(10, 5), sticky=(tk.W, tk.E))


        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="Selected File", padding="10")
        file_frame.grid(row=3, column=0, pady=(0, 20), sticky=(tk.W, tk.E))
        file_frame.grid_columnconfigure(0, weight=1)
        
        # File path display
        self.file_path_var = tk.StringVar(value="No file selected")
        file_path_label = ttk.Label(
            file_frame,
            textvariable=self.file_path_var,
            font=("Arial", 9),
            foreground="gray"
        )
        file_path_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=4, column=0, pady=(0, 20), sticky=(tk.W, tk.E))
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Status display
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Arial", 9)
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
            main_frame,
            text="© 2025 TNS - Internal Use Only",
            font=("Arial", 8),
            foreground="gray"
        )
        footer_label.grid(row=5, column=0, pady=(20, 0))
    
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
                self._update_status("Booking creation process started successfully")
                messagebox.showinfo("Success", "Driver name filled and Next button clicked. Continue in the browser.")
            else:
                error_msg = "Failed to start booking creation. Check the browser and try again."
                self._update_status("Failed to start booking creation")
                messagebox.showerror("Booking Creation Error", error_msg)

        except Exception as e:
            error_msg = f"Error starting booking creation: {str(e)}"
            logger.error(error_msg)
            self._update_status("Error starting booking creation")
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

            # Enable the Start Processing Bookings button
            self.create_bookings_button.config(state="normal")

            # Process file in background thread
            self._update_status("Processing Excel file...")
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
            # Initialize Excel processor if needed
            if not self.excel_processor:
                self.excel_processor = ExcelProcessor()
            
            # Process the file
            result = self.excel_processor.process_file(file_path)
            
            # Update UI on main thread
            self.root.after(0, self._on_file_processed, result)
            
        except Exception as e:
            error_msg = f"Error processing Excel file: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, self._on_processing_error, error_msg)
    
    def _on_file_processed(self, result):
        """Handle successful file processing (runs on main thread)."""
        try:
            if result.success:
                # Store processed data for booking creation
                self.processed_data = result.data

                status_msg = f"File processed successfully. {result.row_count} rows found."
                self._update_status(status_msg)
                self._update_progress(100)

                # Show success message
                messagebox.showinfo(
                    "Success",
                    f"Excel file processed successfully!\n\n"
                    f"Rows processed: {result.row_count}\n"
                    f"Valid rows: {result.valid_rows}\n"
                    f"Invalid rows: {result.invalid_rows}"
                )

            else:
                # Clear processed data on failure and disable button
                self.processed_data = None
                self.create_bookings_button.config(state="disabled")
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
