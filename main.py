import os
import pytesseract
from fastapi import FastAPI

from routers import groq_router, ollama_router


def configure_tesseract():
    """Auto-detect Tesseract installation across platforms."""
    if os.name == "nt":
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tesseract-OCR\tesseract.exe",
        ]
    elif os.uname().sysname == "Darwin":
        possible_paths = [
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",
            "/usr/bin/tesseract",
        ]
    else:
        possible_paths = [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
        ]

    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return


configure_tesseract()

app = FastAPI(title="Text Harvester")
app.include_router(groq_router.router)
app.include_router(ollama_router.router)
