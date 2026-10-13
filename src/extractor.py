from pathlib import Path
import pymupdf

class PDFExtractor:
    @staticmethod
    def extract_text(pdf_path: str, max_pages: int = 10) -> str:
        doc = pymupdf.open(pdf_path)
        extracted_chunks = []
        
        for page_idx in range(min(len(doc), max_pages)):
            page = doc[page_idx]
            # Extract plain text; flags omit some redundant whitespace
            text = page.get_text("text")
            cleaned_text = "\n".join(
                line.strip() for line in text.splitlines() if len(line.strip()) > 3
            )
            extracted_chunks.append(f"--- PAGE {page_idx + 1} ---\n{cleaned_text}")
            
        return "\n\n".join(extracted_chunks)