# ============================= FILE: utils/document_parsers.py =============================
from xml.etree import ElementTree
from docx import Document
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
import warnings
from loguru import logger

def parse_docx(file_path: str) -> str:
    """
    Parse a .docx file into text.
    """
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            paragraph_text = para.text.strip()
            if paragraph_text:
                full_text.append(paragraph_text)
        extracted_text = "\n".join(full_text)
        words_count = len(extracted_text.split())
        logger.info(f"[DOCX] Extracted {words_count} words from {file_path}")
        return extracted_text
    except Exception as e:
        logger.error(f"Error parsing DOCX {file_path}: {e}")
        return ""

def parse_fb2(file_path: str) -> str:
    """
    Parse an .fb2 file into text.
    """
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        data_str = data.decode('utf-8', errors='replace')
        root = ElementTree.fromstring(data_str)
        ns = root.tag.split('}')[0].strip('{')
        namespaces = {'fb2': ns}

        sections = root.findall('.//fb2:section', namespaces=namespaces)
        text_chunks = []
        for sec in sections:
            paragraphs = sec.findall('.//fb2:p', namespaces=namespaces)
            sec_text = "\n".join([p.text.strip() for p in paragraphs if p.text])
            if sec_text.strip():
                text_chunks.append(sec_text)
        extracted_text = "\n\n".join(text_chunks).strip()
        words_count = len(extracted_text.split())
        logger.info(f"[FB2] Extracted {words_count} words from {file_path}")
        return extracted_text
    except Exception as e:
        logger.error(f"Error parsing FB2 {file_path}: {e}")
        return ""

def parse_epub(file_path: str) -> str:
    """
    Parse an .epub file into text.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            book = epub.read_epub(file_path)
        items = list(book.get_items_of_type(ITEM_DOCUMENT))
        logger.info(f"EPUB has {len(items)} document items")
        full_text = []

        for idx, item in enumerate(items, start=1):
            if item.get_type() == ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')
                for bad_tag in soup(["script", "style", "nav", "header", "footer", "meta", "link"]):
                    bad_tag.extract()
                paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                text_only = "\n".join(
                    para.get_text(separator=' ', strip=True) for para in paragraphs
                ).strip()

                logger.debug(f"[EPUB] Part {idx}: extracted {len(text_only.split())} words.")
                if text_only:
                    full_text.append(text_only)

        extracted_text = "\n".join(full_text)
        total_words = len(extracted_text.split())
        logger.info(f"[EPUB] Total extracted words: {total_words}")
        return extracted_text
    except Exception as e:
        logger.error(f"Error parsing EPUB {file_path}: {e}")
        return ""