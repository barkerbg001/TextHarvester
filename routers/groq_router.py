"""Groq-based invoice processing router."""
import json
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from groq import Groq
from dotenv import load_dotenv

from schemas import InvoiceSchema
from utils import extract_text_from_pdf, extract_text_from_image

load_dotenv()

router = APIRouter(prefix="/groq", tags=["Groq"])
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@router.post("/process-invoice", response_model=InvoiceSchema)
async def process_invoice(file: UploadFile = File(...)):
    """Extract structured invoice data using Groq LLM."""
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

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert accountant. Extract invoice data into JSON format. "
                        f"Adhere strictly to this schema: {InvoiceSchema.model_json_schema()}"
                    ),
                },
                {"role": "user", "content": f"Extract data from this text: {raw_text}"},
            ],
            response_format={"type": "json_object"},
        )

        structured_data = json.loads(completion.choices[0].message.content)
        return InvoiceSchema(**structured_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
