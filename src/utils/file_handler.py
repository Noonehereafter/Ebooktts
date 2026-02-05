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

def read_epub(filepath, return_chapters=False):
    """
    Reads an EPUB file.

    Args:
        filepath (str): Path to epub file.
        return_chapters (bool): If True, returns a list of (title, text).
                                If False, returns combined text string.
    """
    try:
        book = epub.read_epub(filepath)

        if not return_chapters:
            text_content = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                    text_content.append(soup.get_text())
            return "\n".join(text_content)
        else:
            chapters = []
            # This is a basic extraction.
            # Real EPUB navigation parsing (toc) is complex, so we iterate documents.
            # We try to find a title, otherwise use "Chapter X"
            count = 1
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                    text = soup.get_text().strip()
                    if text:
                        # Try to find a header as title
                        title = f"Chapter {count}"
                        header = soup.find(['h1', 'h2', 'h3'])
                        if header:
                            title = header.get_text().strip()[:50] # Limit title length

                        chapters.append({'title': title, 'content': text})
                        count += 1
            return chapters

    except Exception as e:
        raise Exception(f"Error reading EPUB file: {e}")

def read_file(filepath, split_chapters=False):
    """Dispatches to the correct reader based on file extension."""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    if ext == '.txt':
        return read_txt(filepath)
    elif ext == '.epub':
        return read_epub(filepath, return_chapters=split_chapters)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
