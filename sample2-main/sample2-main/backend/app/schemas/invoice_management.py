from __future__ import annotations

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
PHONE_PATTERN = re.compile(r"^\+?[0-9 ()-]{7,20}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
STATE_CODE_PATTERN = re.compile(r"^[0-9]{2}$")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _gstin(value: str | None) -> str | None:
    value = _clean(value)
    if value is None:
        return None
    value = value.upper()
    if not GSTIN_PATTERN.match(value):
        raise ValueError("GSTIN must be a valid 15-character GST identification number")
    return value


def _phone(value: str | None) -> str | None:
    value = _clean(value)
    if value is not None and not PHONE_PATTERN.match(value):
        raise ValueError("Phone number is invalid")
    return value


def _email(value: str | None) -> str | None:
    value = _clean(value)
    if value is not None and not EMAIL_PATTERN.match(value):
        raise ValueError("Email address is invalid")
    return value


# ---------- Company Master ----------


class CompanyInput(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    gstin: str = Field(min_length=15, max_length=15)
    pan: str = Field(min_length=10, max_length=10)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    address: str = Field(min_length=1)
    ship_from_address: str | None = None
    bank_name: str | None = Field(default=None, max_length=255)
    bank_account_name: str | None = Field(default=None, max_length=255)
    bank_account_no: str | None = Field(default=None, max_length=64)
    bank_ifsc: str | None = Field(default=None, max_length=16)
    bank_branch: str | None = Field(default=None, max_length=255)

    @field_validator("company_name", "address")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field is required")
        return value

    @field_validator("gstin")
    @classmethod
    def check_gstin(cls, value: str) -> str:
        return _gstin(value) or ""

    @field_validator("pan")
    @classmethod
    def check_pan(cls, value: str) -> str:
        value = value.strip().upper()
        if not PAN_PATTERN.match(value):
            raise ValueError("PAN must be a valid 10-character permanent account number")
        return value

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value: str | None) -> str | None:
        return _phone(value)

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str | None) -> str | None:
        return _email(value)

    @model_validator(mode="after")
    def pan_matches_gstin(self) -> "CompanyInput":
        if self.gstin[2:12] != self.pan:
            raise ValueError("PAN must match characters 3-12 of the GSTIN")
        return self


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: int
    company_name: str
    gstin: str
    pan: str
    phone: str | None
    email: str | None
    address: str
    ship_from_address: str | None
    bank_name: str | None
    bank_account_name: str | None
    bank_account_no: str | None
    bank_ifsc: str | None
    bank_branch: str | None
    created_at: datetime
    updated_at: datetime


# ---------- Customer Master ----------


class CustomerInput(BaseModel):
    customer_name: str = Field(min_length=1, max_length=255)
    gstin: str | None = Field(default=None, max_length=15)
    contact_person: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    billing_address: str = Field(min_length=1)
    shipping_address: str | None = None
    state_code: str = Field(min_length=2, max_length=2)

    @field_validator("customer_name", "billing_address")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field is required")
        return value

    @field_validator("gstin")
    @classmethod
    def check_gstin(cls, value: str | None) -> str | None:
        return _gstin(value)

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value: str | None) -> str | None:
        return _phone(value)

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str | None) -> str | None:
        return _email(value)

    @field_validator("state_code")
    @classmethod
    def check_state_code(cls, value: str) -> str:
        value = value.strip()
        if not STATE_CODE_PATTERN.match(value):
            raise ValueError("State code must be a 2-digit GST state code")
        return value

    @model_validator(mode="after")
    def state_matches_gstin(self) -> "CustomerInput":
        if self.gstin and self.gstin[:2] != self.state_code:
            raise ValueError("State code must match the first two digits of the GSTIN")
        return self


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    customer_name: str
    gstin: str | None
    contact_person: str | None
    phone: str | None
    email: str | None
    billing_address: str
    shipping_address: str | None
    state_code: str
    created_at: datetime
    updated_at: datetime


# ---------- Product Catalog ----------


class ProductInput(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    hsn_sac: str = Field(pattern=r"^[0-9]{4,8}$")
    unit: str = Field(min_length=1, max_length=32)
    rate: float = Field(ge=0)
    gst_percentage: float = Field(ge=0, le=100)

    @field_validator("product_name", "unit")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field is required")
        return value


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str
    hsn_sac: str
    unit: str
    rate: float
    gst_percentage: float
    created_at: datetime
    updated_at: datetime


# ---------- Invoice ----------


class InvoiceItemInput(BaseModel):
    product_id: int = Field(gt=0)
    description: str | None = None
    hsn_sac: str | None = Field(default=None, max_length=16)
    quantity: float = Field(gt=0)
    unit: str | None = Field(default=None, max_length=32)
    rate: float | None = Field(default=None, ge=0)
    gst_percentage: float | None = Field(default=None, ge=0, le=100)


class InvoiceInput(BaseModel):
    invoice_no: str | None = Field(default=None, max_length=64)
    invoice_date: date
    due_date: date | None = None
    po_reference: str | None = Field(default=None, max_length=128)
    place_of_supply: str = Field(min_length=1, max_length=64)
    company_id: int = Field(gt=0)
    customer_id: int = Field(gt=0)
    payment_terms: str | None = Field(default=None, max_length=255)
    terms_and_conditions: str | None = None
    discount_amount: float = Field(default=0, ge=0)
    items: list[InvoiceItemInput] = Field(min_length=1)

    @model_validator(mode="after")
    def due_after_invoice(self) -> "InvoiceInput":
        if self.due_date and self.due_date < self.invoice_date:
            raise ValueError("Due date cannot be before the invoice date")
        return self


class InvoiceCreate(InvoiceInput):
    source: Literal["manual", "email", "chat"] = "manual"


class InvoiceUpdate(InvoiceInput):
    pass


class InvoiceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    line_no: int
    product_id: int
    description: str
    hsn_sac: str
    quantity: float
    unit: str
    rate: float
    gst_percentage: float
    amount: float
    tax_amount: float


class InvoiceSummary(BaseModel):
    invoice_id: int
    invoice_no: str
    invoice_date: date
    due_date: date | None
    po_reference: str | None
    place_of_supply: str
    company_id: int
    customer_id: int
    company_name: str
    customer_name: str
    payment_terms: str | None
    source: str
    subtotal: float
    tax_amount: float
    grand_total: float


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: int
    invoice_no: str
    invoice_date: date
    due_date: date | None
    po_reference: str | None
    place_of_supply: str
    company_id: int
    customer_id: int
    payment_terms: str | None
    terms_and_conditions: str | None
    source: str
    subtotal: float
    discount_amount: float
    taxable_value: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    tax_amount: float
    round_off: float
    grand_total: float
    amount_in_words: str
    created_at: datetime
    updated_at: datetime
    company: CompanyRead
    customer: CustomerRead
    items: list[InvoiceItemRead]


# ---------- Future integration hooks ----------


class InvoiceFromEmailRequest(BaseModel):
    sender: str = Field(min_length=1, max_length=255)
    subject: str = Field(default="", max_length=500)
    body: str = Field(min_length=1, max_length=50_000)


class InvoiceFromChatRequest(BaseModel):
    conversation_id: str | None = Field(default=None, max_length=64)
    messages: list[str] = Field(min_length=1, max_length=200)


class InvoiceDraftResponse(BaseModel):
    status: Literal["not_implemented", "draft_ready"]
    source: Literal["email", "chat"]
    message: str
    draft: InvoiceCreate | None = None
