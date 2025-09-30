#!/usr/bin/env python3
"""
Script to create sample Excel data for testing TNS Booking Uploader Bot.
"""

import pandas as pd
from pathlib import Path

def create_sample_excel():
    """Create a sample Excel file with booking data."""
    
    sample_data = {
        'Date': ['4/9/2025', '4/9/2025', '4/10/2025', '4/10/2025', '4/11/2025'],
        'Time': ['02:09', '02:41', '08:15', '14:30', '16:45'],
        'Driver': ['MAJCEN Dennis', 'JAMES Quin', 'SMITH John', 'DOE Jane', 'BROWN Mike'],
        'From': ['NME', 'FKND', 'CPS03O', 'KANS09', 'NME'],
        'To': ['CPS03O', 'KANS09', 'NME', 'FKND', 'CPS03O'],
        'Reason': ['', '', 'Medical appointment', '', 'Business meeting'],
        'Shift': ['1001', '211', '1002', '212', '1003']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Save to Excel file
    output_path = Path(__file__).parent / 'sample_booking_data.xlsx'
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    print(f"Sample Excel file created: {output_path}")
    print(f"Data shape: {df.shape}")
    print("\nSample data:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    create_sample_excel()
