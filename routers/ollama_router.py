"""Ollama-based invoice processing router."""
import json
import ollama
from fastapi import APIRouter, UploadFile, File, HTTPException

from schemas import InvoiceSchema
from utils import extract_text_from_pdf, extract_text_from_image

router = APIRouter(prefix="/ollama", tags=["Ollama"])


@router.post("/process-invoice", response_model=InvoiceSchema)
async def process_invoice(file: UploadFile = File(...)):
    """Extract structured invoice data using local Ollama LLM."""
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    try:
        contents = await file.read()

        if file.content_type == "application/pdf":
            raw_text = extract_text_from_pdf(contents)
        else:
            raw_text = extract_text_from_image(contents)

        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="No readable text found in document.")

        response = ollama.chat(
            model="llama3",
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
                    ),
                },
                {"role": "user", "content": f"Extract invoice data from this text:\n\n{raw_text}"},
            ],
            format="json",
        )

        response_content = response["message"]["content"].strip()
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
                detail=f"Failed to parse LLM response as JSON: {str(e)}\nResponse was: {response_content[:500]}",
            )

        if "$defs" in structured_data or (
            "type" in structured_data and structured_data.get("type") == "object"
        ):
            raise HTTPException(
                status_code=500,
                detail="LLM returned schema definition instead of invoice data. Please check the prompt.",
            )

        return InvoiceSchema(**structured_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
