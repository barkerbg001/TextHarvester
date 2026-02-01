"""Shared text extraction utilities for PDF and images."""
import io
import fitz  # PyMuPDF
import pytesseract
from PIL import Image


def extract_text_from_pdf(contents: bytes) -> str:
    """Extract text from PDF."""
    text = ""
    with fitz.open(stream=contents, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text


def extract_text_from_image(contents: bytes) -> str:
    """Extract text from image using Tesseract OCR."""
    img = Image.open(io.BytesIO(contents))
    text = pytesseract.image_to_string(img)
    return text
