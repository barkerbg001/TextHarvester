"""Shared Pydantic schemas for invoice extraction."""
from typing import List, Optional
from pydantic import BaseModel, Field


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
