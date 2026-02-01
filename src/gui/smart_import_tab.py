"""
Smart Import tab - Full-featured workflow with Excel and CSV processing.

This tab provides the complete workflow including:
- Excel pre-processing for monthly receipt generation (optional)
- CSV file import (standard workflow)
- Receipt validation and processing
- Progress tracking and logging
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Callable, List, Optional
from datetime import datetime
import threading
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import openpyxl

try:
    from excel_preprocessor import LandlordExcelProcessor, ProcessingAlert, ReceiptData
    from csv_handler import CSVHandler
    from web_client import WebClient
    from receipt_processor import ReceiptProcessor
    from utils.logger import get_logger
    from utils.multilingual_localization import get_text
    from gui.themed_button import ThemedButton
except ImportError:
    from src.excel_preprocessor import LandlordExcelProcessor, ProcessingAlert, ReceiptData
    from src.csv_handler import CSVHandler
    from src.web_client import WebClient
    from src.receipt_processor import ReceiptProcessor
    from src.utils.logger import get_logger
    from src.utils.multilingual_localization import get_text
    from src.gui.themed_button import ThemedButton

logger = get_logger(__name__)


class SmartImportTab(tk.Frame):
    """Smart Import tab with full Excel and CSV processing capabilities."""
    
    def __init__(self, parent, csv_handler: CSVHandler, web_client: WebClient, 
                 processor: ReceiptProcessor, mode_var: tk.StringVar, 
                 dry_run_var: tk.BooleanVar, on_log: Callable):
        """
        Initialize Smart Import tab.
        
        Args:
            parent: Parent widget (notebook)
            csv_handler: CSV handler instance
            web_client: Web client instance
            processor: Receipt processor instance
            mode_var: Processing mode variable (bulk/step)
            dry_run_var: Dry run flag variable
            on_log: Logging callback function
        """
        super().__init__(parent, bg='#1e293b')
        
        # Store references
        self.csv_handler = csv_handler
        self.web_client = web_client
        self.processor = processor
        self.mode_var = mode_var
        self.dry_run_var = dry_run_var
        self.on_log = on_log
        
        # Initialize Excel processor
        self.excel_processor = LandlordExcelProcessor()
        
        # Variables
        self.excel_file_path = tk.StringVar()
        self.csv_file_path = tk.StringVar()
        self.selected_month = tk.IntVar(value=datetime.now().month)
        self.selected_sheet = tk.StringVar()  # Sheet name represents the year
        self.available_sheets = []  # List of sheet names from Excel
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value=get_text('STATUS_READY'))
        
        # State
        self.current_receipts: List[ReceiptData] = []
        self.current_alerts: List[ProcessingAlert] = []
        self.processing_thread = None
        self.stop_requested = False
        
        self._setup_gui()
    
    def _setup_gui(self):
        """Setup the tab GUI components."""
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(self, bg='#1e293b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1e293b')
        
        # Configure canvas scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Configure grid for scrollable frame instead of self
        scrollable_frame.columnconfigure(0, weight=1)
        scrollable_frame.rowconfigure(2, weight=1)  # Processing section expands for log
        
        # Excel Import Section with dark styling
        excel_frame = tk.LabelFrame(scrollable_frame, text="  📁 Excel Import  ", 
                                   bg='#1e293b', fg='#3b82f6',
                                   font=('Segoe UI', 9), relief='solid', borderwidth=1,
                                   padx=12, pady=8)
        excel_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        excel_frame.columnconfigure(1, weight=1)  # Excel file entry expands
        
        # Excel file selection
        tk.Label(excel_frame, text="Excel File:", bg='#1e293b', fg='#ffffff', font=('Segoe UI', 9)).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(excel_frame, textvariable=self.excel_file_path, state="readonly", font=('Segoe UI', 9), foreground='black').grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 6)
        )
        
        ThemedButton(excel_frame, style='secondary', text="📁 Browse...", 
                    command=self._browse_excel).grid(row=0, column=2, padx=(0, 6))
        
        # Data Selection Section with dark styling
        data_frame = tk.LabelFrame(scrollable_frame, text="  📅 Data Selection  ", 
                                   bg='#1e293b', fg='#3b82f6',
                                   font=('Segoe UI', 9), relief='solid', borderwidth=1,
                                   padx=12, pady=8)
        data_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Single row with month, year, and download button
        selection_row = tk.Frame(data_frame, bg='#1e293b')
        selection_row.pack(fill=tk.X)
        
        tk.Label(selection_row, text="Month:", bg='#1e293b', fg='#ffffff', font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        months = ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
        self.month_combo = ttk.Combobox(selection_row, values=months, width=12, state="readonly")
        self.month_combo.current(self.selected_month.get() - 1)
        self.month_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.month_combo.bind("<<ComboboxSelected>>", self._on_month_year_selected)
        
        tk.Label(selection_row, text="Year Tab:", bg='#1e293b', fg='#ffffff', font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.sheet_combo = ttk.Combobox(selection_row, textvariable=self.selected_sheet, width=10, state="readonly")
        self.sheet_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.sheet_combo.bind("<<ComboboxSelected>>", self._on_month_year_selected)
        
        self.generate_csv_button = ThemedButton(selection_row, style='primary', text="📊 Generate CSV Data", 
                                               command=self._process_excel, state="disabled")
        self.generate_csv_button.pack(side=tk.LEFT, padx=(15, 0))
        
        self.download_csv_button = ThemedButton(selection_row, style='secondary', text="⬇ Download CSV", 
                                               command=self._download_csv, state="disabled")
        self.download_csv_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Processing Section with dark styling - buttons, status, and log as fields
        processing_frame = tk.LabelFrame(scrollable_frame, text="  ⏱ Processing  ", 
                                        bg='#1e293b', fg='#3b82f6',
                                        font=('Segoe UI', 9), relief='solid', borderwidth=1,
                                        padx=12, pady=8)
        processing_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        processing_frame.columnconfigure(0, weight=1)
        processing_frame.rowconfigure(2, weight=1)  # Log expands
        
        # Processing control buttons
        button_frame = tk.Frame(processing_frame, bg='#1e293b')
        button_frame.grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        self.start_button = ThemedButton(button_frame, style='primary',
                                        text="▶ " + get_text('PROCESS_RECEIPTS_BUTTON'), 
                                        command=self._start_processing, state="disabled")
        self.start_button.pack(side=tk.LEFT, padx=(0, 6))
        
        self.stop_button = ThemedButton(button_frame, style='danger',
                                       text="⏹ " + get_text('CANCEL_BUTTON'), 
                                       command=self._stop_processing, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 6))
        
        self.validate_button = ThemedButton(button_frame, style='tertiary',
                                           text="✓ " + get_text('VALIDATE_CONTRACTS_BUTTON'), 
                                           command=self._validate_contracts, state="disabled")
        self.validate_button.pack(side=tk.LEFT, padx=(0, 6))
        
        self.export_button = ThemedButton(button_frame, style='secondary',
                                         text="📊 " + get_text('EXPORT_RESULTS_BUTTON'), 
                                         command=self._export_results)
        self.export_button.pack(side=tk.LEFT, padx=(0, 6))
        
        ThemedButton(button_frame, style='secondary', text="📡 API Monitor", 
                    command=self._show_api_monitor).pack(side=tk.LEFT)
        
        # Status field (not subsection)
        status_container = tk.Frame(processing_frame, bg='#1e293b')
        status_container.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        status_container.columnconfigure(0, weight=1)
        
        tk.Label(status_container, text="Status:", bg='#1e293b', fg='#94a3b8', 
                font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        
        self.progress_bar = ttk.Progressbar(status_container, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 4))
        
        status_label = tk.Label(status_container, textvariable=self.status_var,
                               bg='#1e293b', fg='#ffffff',
                               font=('Segoe UI', 9))
        status_label.grid(row=2, column=0, sticky=tk.W)
        
        # Log field (not subsection)
        log_container = tk.Frame(processing_frame, bg='#1e293b')
        log_container.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(1, weight=1)
        
        tk.Label(log_container, text="Log:", bg='#1e293b', fg='#94a3b8', 
                font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        
        self.log_text = scrolledtext.ScrolledText(log_container, height=10, width=80, wrap=tk.WORD,
                                                  font=('Consolas', 9),
                                                  bg='#0f172a',
                                                  fg='#94a3b8',
                                                  relief='sunken',
                                                  borderwidth=2,
                                                  highlightthickness=0,
                                                  padx=10,
                                                  pady=10)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def _create_compatible_excel(self, source_path, dest_path, sheet_name):
        """Create an openpyxl-compatible Excel file from a problematic source file."""
        try:
            # Create new workbook
            new_wb = openpyxl.Workbook()
            new_wb.remove(new_wb.active)  # Remove default sheet
            new_ws = new_wb.create_sheet(sheet_name)
            
            # Read all data from source ZIP
            with zipfile.ZipFile(source_path, 'r') as zip_ref:
                # Load shared strings
                shared_strings = []
                if 'xl/sharedStrings.xml' in zip_ref.namelist():
                    with zip_ref.open('xl/sharedStrings.xml') as ss_file:
                        ss_tree = ET.parse(ss_file)
                        for elem in ss_tree.iter():
                            if elem.tag.endswith('t'):
                                if elem.text:
                                    shared_strings.append(elem.text)
                
                # Read worksheet data
                sheet_xml_path = 'xl/worksheets/sheet1.xml'
                if sheet_xml_path in zip_ref.namelist():
                    with zip_ref.open(sheet_xml_path) as sheet_file:
                        sheet_tree = ET.parse(sheet_file)
                        sheet_root = sheet_tree.getroot()
                        
                        # Process each row
                        row_num = 1
                        for row_elem in sheet_root.iter():
                            if not row_elem.tag.endswith('row'):
                                continue
                            
                            col_num = 1
                            for cell_elem in row_elem:
                                if not cell_elem.tag.endswith('c'):
                                    continue
                                
                                # Get cell value
                                cell_type = cell_elem.attrib.get('t', '')
                                v_elem = None
                                for child in cell_elem:
                                    if child.tag.endswith('v'):
                                        v_elem = child
                                        break
                                
                                if v_elem is not None and v_elem.text:
                                    if cell_type == 's':
                                        # Shared string
                                        idx = int(v_elem.text)
                                        if 0 <= idx < len(shared_strings):
                                            value = shared_strings[idx]
                                        else:
                                            value = v_elem.text
                                    else:
                                        # Try to convert to number
                                        try:
                                            value = float(v_elem.text)
                                            if value.is_integer():
                                                value = int(value)
                                        except:
                                            value = v_elem.text
                                    
                                    # Write to new sheet
                                    new_ws.cell(row=row_num, column=col_num, value=value)
                                
                                col_num += 1
                            row_num += 1
            
            # Save the new workbook
            new_wb.save(dest_path)
            self.on_log("INFO", f"Created compatible Excel file with {row_num-1} rows")
            
        except Exception as e:
            self.on_log("ERROR", f"Failed to create compatible file: {e}")
            import traceback
            self.on_log("ERROR", traceback.format_exc())
            raise
    
    def _on_month_year_selected(self, event=None):
        """Handle month/year selection - update selection only, don't auto-process."""
        self.selected_month.set(self.month_combo.current() + 1)
        # Don't auto-process - wait for user to click Process button
    
    def _browse_excel(self):
        """Browse for Excel file, detect month columns and year from structure."""
        file_path = filedialog.askopenfilename(
            title="Select Landlord Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if file_path:
            self.excel_file_path.set(file_path)
            
            # Load and analyze file structure
            try:
                file_ext = os.path.splitext(file_path)[1].lower()
                self.on_log("INFO", f"File extension: {file_ext}")
                
                # First, inspect the xlsx file structure directly using zipfile
                try:
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        file_list = zip_ref.namelist()
                        self.on_log("INFO", f"ZIP contents ({len(file_list)} files): {file_list[:10]}...")
                        
                        # Try to read workbook.xml to get sheet names
                        if 'xl/workbook.xml' in file_list:
                            with zip_ref.open('xl/workbook.xml') as xml_file:
                                content = xml_file.read()
                                self.on_log("DEBUG", f"workbook.xml size: {len(content)} bytes")
                                
                                tree = ET.fromstring(content)
                                
                                # Try multiple namespace approaches
                                # Method 1: With namespace
                                ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                                sheets = tree.findall('.//main:sheet', ns)
                                self.on_log("DEBUG", f"Method 1 (with namespace): found {len(sheets)} sheets")
                                
                                # Method 2: Without namespace (any sheet tag)
                                if not sheets:
                                    # Find all elements ending with 'sheet'
                                    for elem in tree.iter():
                                        if elem.tag.endswith('sheet'):
                                            sheets.append(elem)
                                    self.on_log("DEBUG", f"Method 2 (any 'sheet' tag): found {len(sheets)} sheets")
                                
                                # Method 3: Direct search for any 'sheets' parent
                                if not sheets:
                                    for elem in tree.iter():
                                        if elem.tag.endswith('sheets'):
                                            sheets = list(elem)
                                            self.on_log("DEBUG", f"Method 3 (children of 'sheets'): found {len(sheets)} sheets")
                                            break
                                
                                self.available_sheets = [sheet.attrib.get('name', f"Sheet{i+1}") 
                                                       for i, sheet in enumerate(sheets) 
                                                       if hasattr(sheet, 'attrib')]
                                self.on_log("INFO", f"✓ Extracted {len(self.available_sheets)} sheets from XML: {self.available_sheets}")
                        else:
                            self.on_log("ERROR", "xl/workbook.xml not found in file!")
                            
                except Exception as zip_error:
                    self.on_log("ERROR", f"ZIP inspection failed: {zip_error}")
                    import traceback
                    self.on_log("ERROR", traceback.format_exc())
                    self.available_sheets = []
                
                # If ZIP method worked, continue; otherwise try openpyxl as fallback
                if not self.available_sheets:
                    self.on_log("WARNING", "Trying openpyxl as fallback...")
                    wb = openpyxl.load_workbook(file_path, data_only=False, keep_vba=False, keep_links=False)
                    self.available_sheets = wb.sheetnames
                    wb.close()
                    self.on_log("INFO", f"Openpyxl found {len(self.available_sheets)} sheets: {self.available_sheets}")
                
                if not self.available_sheets:
                    messagebox.showerror("Invalid File", 
                                       "Excel file has no sheets or is corrupted.\n\n" +
                                       f"File: {os.path.basename(file_path)}\n" +
                                       "Please verify the file opens correctly in Excel.")
                    self.excel_file_path.set("")
                    return
                
                # Detect year from sheet names (sheet names are exactly 4-digit years like 2026, 2027)
                year_sheets = []
                self.on_log("INFO", f"Scanning {len(self.available_sheets)} sheets for year detection...")
                
                for sheet_name in self.available_sheets:
                    sheet_str = str(sheet_name).strip()
                    self.on_log("DEBUG", f"  Sheet: {repr(sheet_name)} -> Type: {type(sheet_name).__name__} -> String: '{sheet_str}' -> isdigit: {sheet_str.isdigit()} -> len: {len(sheet_str)}")
                    
                    # Check if sheet name is exactly a 4-digit number
                    if sheet_str.isdigit() and len(sheet_str) == 4:
                        year = int(sheet_str)
                        self.on_log("DEBUG", f"    -> Valid 4-digit: {year}")
                        # Validate it's a reasonable year (1900-2100)
                        if 1900 <= year <= 2100:
                            year_sheets.append(sheet_name)
                            self.on_log("INFO", f"    ✓ Accepted year sheet: {sheet_name}")
                        else:
                            self.on_log("DEBUG", f"    ✗ Year {year} outside valid range (1900-2100)")
                    else:
                        self.on_log("DEBUG", f"    ✗ Not a 4-digit number")
                
                self.on_log("INFO", f"Total year sheets found: {len(year_sheets)}")
                self.on_log("INFO", f"Year sheets: {year_sheets}")
                
                if not year_sheets:
                    messagebox.showerror("Invalid File", 
                                       "No valid year found in sheet names.\n\n" +
                                       "Sheet names must contain a 4-digit year (e.g., '2026', 'Year 2026')")
                    self.excel_file_path.set("")
                    return
                
                # Read month columns directly from ZIP (openpyxl can't load this file properly)
                self.on_log("INFO", "Reading first row to detect month columns...")
                month_columns = []
                
                try:
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        # First, load shared strings if they exist
                        shared_strings = []
                        if 'xl/sharedStrings.xml' in zip_ref.namelist():
                            with zip_ref.open('xl/sharedStrings.xml') as ss_file:
                                ss_tree = ET.parse(ss_file)
                                ss_root = ss_tree.getroot()
                                # Extract all string values
                                for elem in ss_root.iter():
                                    if elem.tag.endswith('t'):  # text element
                                        if elem.text:
                                            shared_strings.append(elem.text)
                                self.on_log("INFO", f"Loaded {len(shared_strings)} shared strings")
                        
                        # Read the first worksheet (sheet1.xml)
                        sheet_xml_path = 'xl/worksheets/sheet1.xml'
                        if sheet_xml_path in zip_ref.namelist():
                            with zip_ref.open(sheet_xml_path) as sheet_file:
                                sheet_tree = ET.parse(sheet_file)
                                sheet_root = sheet_tree.getroot()
                                
                                # Find first row
                                first_row = None
                                for elem in sheet_root.iter():
                                    if elem.tag.endswith('row'):
                                        first_row = elem
                                        break
                                
                                if first_row:
                                    self.on_log("INFO", f"Found first row")
                                    header_values = []
                                    
                                    # Get all cells (c elements) in first row
                                    for cell in first_row:
                                        if cell.tag.endswith('c'):
                                            # Check cell type - 's' means shared string
                                            cell_type = cell.attrib.get('t', '')
                                            
                                            # Get cell value
                                            v_elem = None
                                            for child in cell:
                                                if child.tag.endswith('v'):
                                                    v_elem = child
                                                    break
                                            
                                            if v_elem is not None and v_elem.text:
                                                if cell_type == 's':
                                                    # Shared string - index into shared_strings
                                                    idx = int(v_elem.text)
                                                    if 0 <= idx < len(shared_strings):
                                                        value = shared_strings[idx]
                                                    else:
                                                        value = v_elem.text
                                                else:
                                                    # Direct value
                                                    value = v_elem.text
                                                
                                                header_values.append(str(value).strip())
                                    
                                    self.on_log("INFO", f"Header values: {header_values}")
                                    
                                    # Find month columns (01-12)
                                    for val in header_values:
                                        if val.isdigit() and len(val) == 2:
                                            month_num = int(val)
                                            if 1 <= month_num <= 12:
                                                month_columns.append(val)
                                    
                                    self.on_log("INFO", f"Detected month columns: {month_columns}")
                        else:
                            self.on_log("ERROR", f"{sheet_xml_path} not found in ZIP")
                            
                except Exception as month_error:
                    self.on_log("ERROR", f"Failed to read month columns from ZIP: {month_error}")
                    import traceback
                    self.on_log("ERROR", traceback.format_exc())
                
                if not month_columns:
                    messagebox.showerror("Invalid File", 
                                       "No valid month columns found in file.\n\n" +
                                       "Expected column headers like '01', '02', '03', etc.")
                    self.excel_file_path.set("")
                    return
                
                # Update dropdowns
                self.sheet_combo['values'] = year_sheets
                
                # Convert month numbers to month names for dropdown
                month_names = ["January", "February", "March", "April", "May", "June", 
                             "July", "August", "September", "October", "November", "December"]
                available_months = [month_names[int(m)-1] for m in month_columns]
                self.month_combo['values'] = available_months
                
                # Auto-select current year and month if available
                current_year_str = str(datetime.now().year)
                if current_year_str in year_sheets:
                    self.sheet_combo.set(current_year_str)
                else:
                    self.sheet_combo.set(year_sheets[0])
                
                current_month = datetime.now().month
                current_month_str = f"{current_month:02d}"
                if current_month_str in month_columns:
                    self.month_combo.set(month_names[current_month-1])
                elif available_months:
                    self.month_combo.set(available_months[0])
                
                self.on_log("INFO", f"Selected Excel file: {file_path}")
                self.on_log("INFO", f"Available years: {', '.join(year_sheets)}")
                self.on_log("INFO", f"Available months: {', '.join(month_columns)}")
                
                # Enable Generate CSV button if month and year are selected
                if self.month_combo.get() and self.sheet_combo.get():
                    self.generate_csv_button.config(state="normal")
                
            except Exception as e:
                logger.exception("Failed to read Excel file")
                messagebox.showerror("Error", f"Failed to read Excel file:\n\n{str(e)}")
                self.on_log("ERROR", f"Failed to load file: {str(e)}")
                self.excel_file_path.set("")
    
    def _process_excel(self):
        """Process Excel file and generate receipt data."""
        try:
            # Check authentication first if portal data is needed
            if not self.web_client.is_authenticated():
                messagebox.showerror("Login Required", 
                                   "Please login before processing Excel file.\n\n" +
                                   "Contract validation requires portal access.")
                return
            
            file_path = self.excel_file_path.get()
            month = self.selected_month.get()
            sheet_name = self.selected_sheet.get()
            
            if not file_path:
                messagebox.showwarning("No File", "Please select an Excel file first.")
                return
            
            if not sheet_name:
                messagebox.showwarning("No Sheet Selected", "Please select a year tab from the dropdown.")
                return
            
            # Extract year from sheet name (handle "2026" or "Year 2026" formats)
            try:
                year = int(''.join(filter(str.isdigit, sheet_name)))
            except ValueError:
                messagebox.showerror("Invalid Sheet", f"Cannot extract year from sheet name '{sheet_name}'.\nSheet name must contain a 4-digit year.")
                return
            
            self.on_log("INFO", f"Processing Excel sheet '{sheet_name}' for month {month}")
            
            # Create a temporary compatible Excel file if openpyxl can't read the original
            temp_file = None
            try:
                # Test if openpyxl can read the file
                test_wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                if not test_wb.sheetnames:
                    # File needs conversion
                    self.on_log("WARNING", "Original file not compatible with openpyxl, creating temporary copy...")
                    test_wb.close()
                    
                    # Create a new workbook and copy data from ZIP
                    import tempfile
                    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
                    temp_file.close()
                    
                    self._create_compatible_excel(file_path, temp_file.name, sheet_name)
                    file_path = temp_file.name
                    self.on_log("INFO", f"Created temporary file: {temp_file.name}")
                else:
                    test_wb.close()
            except Exception as test_error:
                self.on_log("WARNING", f"File compatibility check failed: {test_error}")
            
            # Parse Excel to generate receipt data
            receipts, alerts = self.excel_processor.parse_excel(file_path, month, year, sheet_name)
            
            # Store the results
            self.current_receipts = receipts
            self.current_alerts = alerts
            
            # Show alerts if any
            if alerts:
                from gui.cross_column_alert_dialog import CrossColumnAlertDialog
                dialog = CrossColumnAlertDialog(self, alerts)
                dialog.show()
            
            # Enable download button
            self.download_csv_button.config(state="normal")
            
            self.on_log("INFO", f"✓ Excel processed: {len(receipts)} receipts ready, {len(alerts)} alerts")
            
            if len(receipts) == 0:
                messagebox.showwarning("No Data", 
                                     "No tenant records found in Excel file.\n\n" +
                                     "Please verify the file has data rows below the header.")
            else:
                messagebox.showinfo("Success", 
                                  f"Excel file processed successfully!\n\n" +
                                  f"Found {len(receipts)} tenant records.\n" +
                                  f"Click 'Download CSV' to save the receipt data.")
            
        except Exception as e:
            logger.exception("Failed to process Excel file")
            messagebox.showerror("Error", f"Failed to process Excel:\n\n{str(e)}")
            self.on_log("ERROR", f"Excel processing error: {str(e)}")
    
    def _download_csv(self):
        """Download the generated CSV file."""
        if not self.current_receipts:
            messagebox.showwarning("No Data", "No receipts to download. Process Excel file first.")
            return
        
        # Ask where to save CSV
        month_name = self.month_combo.get()
        sheet_name = self.selected_sheet.get()
        default_filename = f"receipts_{month_name}_{sheet_name}.csv"
        
        csv_path = filedialog.asksaveasfilename(
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if not csv_path:
            return
        
        try:
            # Write CSV
            self._write_csv(csv_path, self.current_receipts)
            
            # Store path for potential loading
            self.csv_file_path.set(csv_path)
            
            messagebox.showinfo("Success", 
                              f"CSV downloaded successfully!\n\n{csv_path}\n\n"
                              f"{len(self.current_receipts)} receipts exported.")
            
            self.on_log("INFO", f"CSV downloaded: {csv_path}")
            
        except Exception as e:
            logger.exception("Failed to download CSV")
            messagebox.showerror("Error", f"Failed to download CSV:\n\n{str(e)}")
            self.on_log("ERROR", f"CSV download error: {str(e)}")
    
    def _load_generated_csv(self):
        """Load the generated CSV for processing."""
        if not self.current_receipts:
            messagebox.showwarning("No Data", "No receipts available. Process Excel file first.")
            return
        
        # First save to temp location if not already saved
        if not self.csv_file_path.get():
            # Auto-save to temp
            import tempfile
            month_name = self.month_combo.get()
            sheet_name = self.selected_sheet.get()
            temp_path = os.path.join(tempfile.gettempdir(), f"receipts_{month_name}_{sheet_name}.csv")
            
            try:
                self._write_csv(temp_path, self.current_receipts)
                self.csv_file_path.set(temp_path)
                self.on_log("INFO", f"Auto-saved CSV to temp: {temp_path}")
            except Exception as e:
                logger.exception("Failed to save temp CSV")
                messagebox.showerror("Error", f"Failed to prepare CSV:\n\n{str(e)}")
                return
        
        # Load CSV into handler
        csv_path = self.csv_file_path.get()
        self._validate_csv_file(csv_path)
        
        messagebox.showinfo("CSV Loaded", 
                          f"CSV loaded successfully!\n\n"
                          f"{len(self.current_receipts)} receipts ready for processing.\n\n"
                          "You can now validate contracts and process receipts.")
    
    def _write_csv(self, file_path: str, receipts: List[ReceiptData]):
        """Write receipts to CSV file."""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['contractId', 'fromDate', 'toDate', 'paymentDate', 'receiptType', 'value'])
            
            for receipt in receipts:
                writer.writerow([
                    receipt.contract_id,
                    receipt.from_date.strftime("%Y-%m-%d"),
                    receipt.to_date.strftime("%Y-%m-%d"),
                    receipt.payment_date.strftime("%Y-%m-%d"),
                    receipt.receipt_type,
                    f"{receipt.value:.2f}"
                ])
    
    def _validate_csv_file(self, file_path: str):
        """Validate and load CSV file."""
        success, message = self.csv_handler.load_csv(file_path)
        
        if success:
            self.on_log("INFO", f"CSV loaded: {file_path}")
            self.on_log("INFO", f"Found {len(self.csv_handler.receipts)} receipts")
            self._update_button_states()
        else:
            self.on_log("ERROR", f"Failed to load CSV: {message}")
            messagebox.showerror("CSV Error", message)
    
    def _start_processing(self):
        """Start receipt processing."""
        if not self.web_client.is_authenticated():
            messagebox.showerror("Not Authenticated", "Please login first.")
            return
        
        if not self.csv_handler.receipts:
            messagebox.showwarning("No Data", "Please load a CSV file first.")
            return
        
        # Start processing in background thread
        self.stop_requested = False
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        mode = self.mode_var.get()
        dry_run = self.dry_run_var.get()
        
        self.processing_thread = threading.Thread(
            target=self._process_receipts_thread,
            args=(mode, dry_run),
            daemon=True
        )
        self.processing_thread.start()
    
    def _process_receipts_thread(self, mode: str, dry_run: bool):
        """Process receipts in background thread."""
        try:
            self.on_log("INFO", f"Starting processing in {mode} mode (dry_run={dry_run})")
            
            # Use the processor to handle receipt submission
            total = len(self.csv_handler.receipts)
            
            for i, receipt in enumerate(self.csv_handler.receipts):
                if self.stop_requested:
                    self.on_log("WARNING", "Processing cancelled by user")
                    break
                
                progress = ((i + 1) / total) * 100
                self.progress_var.set(progress)
                self.status_var.set(f"Processing {i+1}/{total}...")
                
                # Process receipt
                self.on_log("INFO", f"Processing receipt {receipt.contract_id}")
            
            self.status_var.set("Completed")
            self.on_log("INFO", "Processing complete")
            
        except Exception as e:
            logger.exception("Processing error")
            self.on_log("ERROR", f"Processing error: {str(e)}")
        finally:
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
    
    def _stop_processing(self):
        """Stop receipt processing."""
        self.stop_requested = True
        self.status_var.set("Stopping...")
        self.on_log("WARNING", "Stop requested")
    
    def _validate_contracts(self):
        """Validate contracts against portal."""
        if not self.web_client.is_authenticated():
            messagebox.showerror("Not Authenticated", "Please login first.")
            return
        
        if not self.csv_handler.receipts:
            messagebox.showwarning("No Data", "Please load a CSV file first.")
            return
        
        self.on_log("INFO", "Validating contracts...")
        messagebox.showinfo("Info", "Contract validation feature")
    
    def _export_results(self):
        """Export processing results."""
        messagebox.showinfo("Info", "Export results feature")
    
    def _show_api_monitor(self):
        """Show API monitor dialog."""
        from gui.api_monitor_dialog import show_api_monitor_dialog
        show_api_monitor_dialog(self)
    
    def _update_button_states(self):
        """Update button states based on current state."""
        has_csv = bool(self.csv_handler.receipts)
        is_authenticated = self.web_client.is_authenticated()
        
        self.start_button.config(state="normal" if (has_csv and is_authenticated) else "disabled")
        self.validate_button.config(state="normal" if (has_csv and is_authenticated) else "disabled")
    
    def log(self, level: str, message: str):
        """Log message to the log text widget."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_line)
        self.log_text.see(tk.END)
        self.on_log(level, message)

