import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def read_txt(filepath):
    """Reads a text file and returns its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Error reading TXT file: {e}")

def read_epub(filepath):
    """Reads an EPUB file and returns the text content from chapters."""
    try:
        book = epub.read_epub(filepath)
        text_content = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                text_content.append(soup.get_text())

        return "\n".join(text_content)
    except Exception as e:
        raise Exception(f"Error reading EPUB file: {e}")

def read_file(filepath):
    """Dispatches to the correct reader based on file extension."""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    if ext == '.txt':
        return read_txt(filepath)
    elif ext == '.epub':
        return read_epub(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
