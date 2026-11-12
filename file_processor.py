import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_files")
os.makedirs(TEMP_DIR, exist_ok=True)

def extract_text_from_docx(file_path: str) -> str:
    """DOCX faylidan matn va jadvallarni ajratib oladi."""
    try:
        import docx
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        
        # Jadvallarni ham o'qish
        tables_text = []
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    tables_text.append(row_text)
                    
        full_content = "\n".join(paragraphs)
        if tables_text:
            full_content += "\n\n[Jadvallar]:\n" + "\n".join(tables_text)
        return full_content.strip()
    except Exception as e:
        logger.error(f"DOCX o'qishda xatolik: {e}")
        return ""

def extract_text_from_excel(file_path: str) -> str:
    """XLSX / XLS faylidan sahifalar va jadvallarni ajratib oladi."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheets_content = []
        
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            rows_data = []
            for row in sheet.iter_rows(values_only=True):
                # Bo'sh bo'lmagan qatorlar
                non_empty = [str(cell).strip() for cell in row if cell is not None and str(cell).strip() != ""]
                if non_empty:
                    rows_data.append(" | ".join(non_empty))
            
            if rows_data:
                sheet_text = f"--- Sahifa: {sheet_name} ---\n" + "\n".join(rows_data[:500])  # Maksimal 500 qator
                sheets_content.append(sheet_text)
                
        return "\n\n".join(sheets_content).strip()
    except Exception as e:
        logger.error(f"Excel o'qishda xatolik: {e}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    """Oddiy matn yoki CSV fayllarini o'qish."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"TXT o'qishda xatolik: {e}")
        return ""
