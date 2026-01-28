import io
import json
import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
import ollama

# Configure Tesseract path for all platforms (if not in PATH)
def configure_tesseract():
    """Auto-detect Tesseract installation across platforms."""
    # Common installation paths by OS
    if os.name == 'nt':  # Windows
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe',
        ]
    elif os.uname().sysname == 'Darwin':  # macOS
        possible_paths = [
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',
            '/usr/bin/tesseract',
        ]
    else:  # Linux
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return
    
    # If not found, assume it's in PATH (will error if not installed)

configure_tesseract()

# --- 1. Define Your Schema ---
class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

class InvoiceSchema(BaseModel):
    doc_number: str = Field(..., description="Invoice or Reference number")
    supplier: str = Field(..., description="Name of the vendor or supplier")
    business_unit: Optional[str] = Field(None, description="Internal department/unit location")
    items: List[InvoiceItem] = Field(default_factory=list)
    subtotal: float
    tax_amount: float
    total_amount: float

# --- 2. Initialize App & Clients ---
app = FastAPI(title="Text Harvester")
# Ollama runs locally - no API key needed
# Make sure Ollama is running: `ollama serve`

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

# --- 3. The Main Endpoint ---
@app.post("/process-invoice", response_model=InvoiceSchema)
async def process_invoice(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    try:
        # Read and Extract
        contents = await file.read()
        
        if file.content_type == "application/pdf":
            raw_text = extract_text_from_pdf(contents)
        else:  # image
            raw_text = extract_text_from_image(contents)
        
        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="No readable text found in document.")

        # Ollama LLM Structuring
        schema_description = {
            "doc_number": "Invoice or Reference number (required string)",
            "supplier": "Name of the vendor or supplier (required string)",
            "business_unit": "Internal department/unit location (optional string)",
            "items": "List of invoice items, each with: description (string), quantity (number), unit_price (number), total (number)",
            "subtotal": "Subtotal amount before tax (required number)",
            "tax_amount": "Tax amount (required number)",
            "total_amount": "Total amount including tax (required number)"
        }
        
        response = ollama.chat(
            model="llama3",  # Use any model you have installed: llama3.2, mistral, etc.
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an expert accountant. Extract invoice data from the provided text and return ONLY a valid JSON object. "
                        "Do NOT return the schema definition. Return actual extracted invoice data.\n\n"
                        "Required fields:\n"
                        "- doc_number: Invoice or Reference number (string)\n"
                        "- supplier: Name of the vendor or supplier (string)\n"
                        "- subtotal: Subtotal amount before tax (number)\n"
                        "- tax_amount: Tax amount (number)\n"
                        "- total_amount: Total amount including tax (number)\n"
                        "- items: Array of items, each with description (string), quantity (number), unit_price (number), total (number)\n\n"
                        "Optional fields:\n"
                        "- business_unit: Internal department/unit location (string or null)\n\n"
                        "If a field cannot be found in the text, use reasonable defaults (empty string for strings, 0 for numbers, empty array for items)."
                    )
                },
                {"role": "user", "content": f"Extract invoice data from this text:\n\n{raw_text}"}
            ],
            format="json"
        )
        
        # Load JSON and validate against Pydantic
        response_content = response["message"]["content"].strip()
        
        # Remove markdown code blocks if present
        if response_content.startswith("```json"):
            response_content = response_content[7:]
        if response_content.startswith("```"):
            response_content = response_content[3:]
        if response_content.endswith("```"):
            response_content = response_content[:-3]
        response_content = response_content.strip()
        
        try:
            structured_data = json.loads(response_content)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to parse LLM response as JSON: {str(e)}\nResponse was: {response_content[:500]}"
            )
        
        # Validate that we got actual data, not a schema definition
        if "$defs" in structured_data or "type" in structured_data and structured_data.get("type") == "object":
            raise HTTPException(
                status_code=500,
                detail="LLM returned schema definition instead of invoice data. Please check the prompt."
            )
        
        return InvoiceSchema(**structured_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")