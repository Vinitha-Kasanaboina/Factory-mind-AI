import os
import re
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(file_path, file_type):
    """
    Extracts raw text and page-by-page mapping from PDF, DOCX, Images, or TXT files.
    Returns: (full_text: str, page_map: list of (page_num, text_str))
    """
    if not os.path.exists(file_path):
        return "", []

    ext = os.path.splitext(file_path)[1].lower()
    page_map = []
    full_text_list = []

    try:
        # PDF Parsing with PyMuPDF (fitz)
        if ext == '.pdf' or file_type == 'PDF':
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text("text") or ""
                    # Fallback to OCR if page has no selectable text
                    if len(text.strip()) < 10:
                        try:
                            import pytesseract
                            from PIL import Image
                            pix = page.get_pixmap()
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            ocr_text = pytesseract.image_to_string(img)
                            if ocr_text.strip():
                                text = ocr_text
                        except Exception as e:
                            logger.warning(f"PyTesseract PDF page OCR skipped: {e}")
                    
                    cleaned = clean_text(text)
                    page_map.append((page_num + 1, cleaned))
                    full_text_list.append(cleaned)
                doc.close()
            except ImportError:
                logger.error("PyMuPDF (fitz) is not installed.")

        # DOCX Parsing
        elif ext in ['.docx', '.doc'] or file_type == 'DOCX':
            try:
                import docx
                doc = docx.Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                cleaned = clean_text(text)
                page_map.append((1, cleaned))
                full_text_list.append(cleaned)
            except Exception as e:
                logger.error(f"DOCX extraction failed: {e}")

        # Image OCR (PNG/JPG)
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff'] or file_type == 'IMAGE':
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
                cleaned = clean_text(text)
                page_map.append((1, cleaned))
                full_text_list.append(cleaned)
            except Exception as e:
                logger.warning(f"Tesseract OCR image extraction error: {e}")
                # Fallback info if Tesseract binary is not on PATH
                msg = f"[Scanned Image File: {os.path.basename(file_path)}. OCR engine requires Tesseract installed on system PATH.]"
                page_map.append((1, msg))
                full_text_list.append(msg)

        # Plain Text / Markdown
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                cleaned = clean_text(text)
                page_map.append((1, cleaned))
                full_text_list.append(cleaned)

    except Exception as exc:
        logger.error(f"Error extracting text from {file_path}: {exc}")

    full_text = "\n\n".join(full_text_list).strip()
    return full_text, page_map


def clean_text(text):
    """Clean whitespace and unwanted control characters."""
    if not text:
        return ""
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def generate_chunks(page_map, chunk_size=500, chunk_overlap=100):
    """
    Splits page text into overlapping passages with page number metadata.
    Returns: list of dicts [{'index': int, 'content': str, 'page_number': int}]
    """
    chunks = []
    chunk_index = 0

    for page_num, text in page_map:
        if not text.strip():
            continue
        words = text.split()
        if not words:
            continue

        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_text = " ".join(words[start:end])
            
            if chunk_text.strip():
                chunks.append({
                    'index': chunk_index,
                    'content': chunk_text,
                    'page_number': page_num
                })
                chunk_index += 1
                
            if end >= len(words):
                break
            start += (chunk_size - chunk_overlap)

    return chunks


def summarize_text(text, max_sentences=3):
    """Generates an extractive text summary."""
    if not text or len(text) < 50:
        return text or "No extractable text content."

    sentences = re.split(r'(?<=[.!?]) +', text)
    cleaned_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    if not cleaned_sentences:
        return text[:300] + "..."

    summary = " ".join(cleaned_sentences[:max_sentences])
    if len(summary) > 400:
        summary = summary[:400] + "..."
    return summary
