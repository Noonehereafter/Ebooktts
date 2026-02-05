import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import pysubs2

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
            count = 1
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                    text = soup.get_text().strip()
                    if text:
                        title = f"Chapter {count}"
                        header = soup.find(['h1', 'h2', 'h3'])
                        if header:
                            title = header.get_text().strip()[:50]

                        chapters.append({'title': title, 'content': text})
                        count += 1
            return chapters

    except Exception as e:
        raise Exception(f"Error reading EPUB file: {e}")

def read_subtitle(filepath):
    """
    Reads a subtitle file (SRT, VTT, etc) and returns structured segments.

    Returns:
        list[dict]: List of segments [{'start': ms, 'end': ms, 'text': str}]
    """
    try:
        subs = pysubs2.load(filepath)
        segments = []
        for line in subs:
            # line.start and line.end are in milliseconds
            text = line.text.replace(r"\N", " ").strip() # Clean subtitle line breaks
            segments.append({
                'start': line.start,
                'end': line.end,
                'text': text
            })
        return segments
    except Exception as e:
        raise Exception(f"Error reading Subtitle file: {e}")

def read_file(filepath, split_chapters=False):
    """Dispatches to the correct reader based on file extension."""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    if ext == '.txt':
        return read_txt(filepath)
    elif ext == '.epub':
        return read_epub(filepath, return_chapters=split_chapters)
    elif ext in ['.srt', '.vtt', '.ass', '.ssa']:
        return read_subtitle(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
