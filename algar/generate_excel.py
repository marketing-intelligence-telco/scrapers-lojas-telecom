import pandas as pd
import os
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
EXTRACTION_DATE = datetime.now().strftime("%Y-%m-%d")

def convert_csv_to_excel(csv_filename, excel_filename):
    if not os.path.exists(csv_filename):
        print(f"[ERROR] ❌ The file '{csv_filename}' was not found in the current directory.")
        return

    print(f"🔄 Reading '{csv_filename}'...")
    
    try:
        # We use on_bad_lines='skip' just in case there are any malformed rows 
        # (e.g., unescaped commas inside an address column)
        df = pd.read_csv(csv_filename, encoding='utf-8', on_bad_lines='warn')
        
        print(f"💾 Converting to '{excel_filename}'...")
        # Write to Excel without the index column
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        
        print(f"✅ [SUCCESS] Excel file successfully generated: {excel_filename}")
        
    except Exception as e:
        print(f"[ERROR] ❌ Failed to convert file: {e}")

if __name__ == "__main__":
    input_csv = OUTPUT_DIR / f"algar_Capilaridade_{EXTRACTION_DATE}.csv"
    output_excel = OUTPUT_DIR / f"algar_Capilaridade_{EXTRACTION_DATE}.xlsx"
    
    convert_csv_to_excel(input_csv, output_excel)