from __future__ import annotations

import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import CompanyMaster, InvoiceCustomerMaster, InvoiceHeader, InvoiceItem, ProductCatalog
from backend.app.schemas.invoice_management import (
    CompanyInput,
    CustomerInput,
    InvoiceCreate,
    InvoiceInput,
    ProductInput,
)

_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
    "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen",
]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _two_digits(number: int) -> str:
    if number < 20:
        return _ONES[number]
    return f"{_TENS[number // 10]} {_ONES[number % 10]}".strip()


def _three_digits(number: int) -> str:
    hundred, rest = divmod(number, 100)
    parts = []
    if hundred:
        parts.append(f"{_ONES[hundred]} Hundred")
    if rest:
        parts.append(_two_digits(rest))
    return " ".join(parts)


def _integer_to_indian_words(number: int) -> str:
    if number == 0:
        return "Zero"
    parts = []
    crore, number = divmod(number, 10_000_000)
    lakh, number = divmod(number, 100_000)
    thousand, number = divmod(number, 1_000)
    if crore:
        parts.append(f"{_integer_to_indian_words(crore)} Crore")
    if lakh:
        parts.append(f"{_two_digits(lakh)} Lakh")
    if thousand:
        parts.append(f"{_two_digits(thousand)} Thousand")
    if number:
        parts.append(_three_digits(number))
    return " ".join(parts)


def amount_to_words(amount: float) -> str:
    paise_total = int(round(abs(amount) * 100))
    rupees, paise = divmod(paise_total, 100)
    words = f"Indian Rupees {_integer_to_indian_words(rupees)}"
    if paise:
        words += f" and {_two_digits(paise)} Paise"
    return f"{words} Only"


# ---------- Generic helpers ----------


def _get_or_404(db: Session, model: type, key: int, label: str):
    record = db.get(model, key)
    if record is None:
        raise HTTPException(status_code=404, detail=f"{label} {key} was not found")
    return record


def _apply(record: object, payload: dict) -> None:
    for field, value in payload.items():
        setattr(record, field, value)


def _search_filter(columns: list, search: str | None):
    if not search or not search.strip():
        return None
    pattern = f"%{search.strip()}%"
    return or_(*(column.ilike(pattern) for column in columns))


# ---------- Company Master ----------


def list_companies(db: Session, search: str | None = None) -> list[CompanyMaster]:
    query = select(CompanyMaster).order_by(CompanyMaster.company_name)
    condition = _search_filter(
        [CompanyMaster.company_name, CompanyMaster.gstin, CompanyMaster.pan, CompanyMaster.email, CompanyMaster.phone],
        search,
    )
    if condition is not None:
        query = query.where(condition)
    return list(db.scalars(query))


def get_company(db: Session, company_id: int) -> CompanyMaster:
    return _get_or_404(db, CompanyMaster, company_id, "Company")


def _ensure_unique_company_gstin(db: Session, gstin: str, exclude_id: int | None = None) -> None:
    query = select(CompanyMaster.company_id).where(CompanyMaster.gstin == gstin)
    if exclude_id is not None:
        query = query.where(CompanyMaster.company_id != exclude_id)
    if db.scalar(query) is not None:
        raise HTTPException(status_code=409, detail=f"A company with GSTIN {gstin} already exists")


def create_company(db: Session, payload: CompanyInput) -> CompanyMaster:
    _ensure_unique_company_gstin(db, payload.gstin)
    company = CompanyMaster(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def update_company(db: Session, company_id: int, payload: CompanyInput) -> CompanyMaster:
    company = get_company(db, company_id)
    _ensure_unique_company_gstin(db, payload.gstin, exclude_id=company_id)
    _apply(company, payload.model_dump())
    db.commit()
    db.refresh(company)
    return company


def delete_company(db: Session, company_id: int) -> None:
    company = get_company(db, company_id)
    if db.scalar(select(func.count()).where(InvoiceHeader.company_id == company_id)):
        raise HTTPException(status_code=409, detail="Company is used on existing invoices and cannot be deleted")
    db.delete(company)
    db.commit()


# ---------- Customer Master ----------


def list_customers(db: Session, search: str | None = None) -> list[InvoiceCustomerMaster]:
    query = select(InvoiceCustomerMaster).order_by(InvoiceCustomerMaster.customer_name)
    condition = _search_filter(
        [
            InvoiceCustomerMaster.customer_name,
            InvoiceCustomerMaster.gstin,
            InvoiceCustomerMaster.contact_person,
            InvoiceCustomerMaster.email,
            InvoiceCustomerMaster.phone,
        ],
        search,
    )
    if condition is not None:
        query = query.where(condition)
    return list(db.scalars(query))


def get_customer(db: Session, customer_id: int) -> InvoiceCustomerMaster:
    return _get_or_404(db, InvoiceCustomerMaster, customer_id, "Customer")


def create_customer(db: Session, payload: CustomerInput) -> InvoiceCustomerMaster:
    customer = InvoiceCustomerMaster(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, customer_id: int, payload: CustomerInput) -> InvoiceCustomerMaster:
    customer = get_customer(db, customer_id)
    _apply(customer, payload.model_dump())
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, customer_id: int) -> None:
    customer = get_customer(db, customer_id)
    if db.scalar(select(func.count()).where(InvoiceHeader.customer_id == customer_id)):
        raise HTTPException(status_code=409, detail="Customer is used on existing invoices and cannot be deleted")
    db.delete(customer)
    db.commit()


# ---------- Product Catalog ----------


def list_products(db: Session, search: str | None = None) -> list[ProductCatalog]:
    query = select(ProductCatalog).order_by(ProductCatalog.product_name)
    condition = _search_filter([ProductCatalog.product_name, ProductCatalog.hsn_sac], search)
    if condition is not None:
        query = query.where(condition)
    return list(db.scalars(query))


def get_product(db: Session, product_id: int) -> ProductCatalog:
    return _get_or_404(db, ProductCatalog, product_id, "Product")


def create_product(db: Session, payload: ProductInput) -> ProductCatalog:
    product = ProductCatalog(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, payload: ProductInput) -> ProductCatalog:
    product = get_product(db, product_id)
    _apply(product, payload.model_dump())
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    if db.scalar(select(func.count()).where(InvoiceItem.product_id == product_id)):
        raise HTTPException(status_code=409, detail="Product is used on existing invoices and cannot be deleted")
    db.delete(product)
    db.commit()


# ---------- Invoices ----------


def _state_code_of_supply(place_of_supply: str, customer: InvoiceCustomerMaster) -> str:
    match = re.match(r"^\s*([0-9]{2})", place_of_supply)
    return match.group(1) if match else customer.state_code


def _build_items(db: Session, payload: InvoiceInput) -> list[InvoiceItem]:
    items = []
    for index, line in enumerate(payload.items, start=1):
        product = get_product(db, line.product_id)
        rate = product.rate if line.rate is None else line.rate
        gst = product.gst_percentage if line.gst_percentage is None else line.gst_percentage
        amount = round(line.quantity * rate, 2)
        items.append(
            InvoiceItem(
                line_no=index,
                product_id=product.product_id,
                description=(line.description or "").strip() or product.product_name,
                hsn_sac=(line.hsn_sac or "").strip() or product.hsn_sac,
                quantity=line.quantity,
                unit=(line.unit or "").strip() or product.unit,
                rate=rate,
                gst_percentage=gst,
                amount=amount,
                tax_amount=round(amount * gst / 100, 2),
            )
        )
    return items


def _apply_totals(invoice: InvoiceHeader, company: CompanyMaster, customer: InvoiceCustomerMaster) -> None:
    subtotal = round(sum(item.amount for item in invoice.items), 2)
    discount = round(invoice.discount_amount or 0, 2)
    if discount > subtotal:
        raise HTTPException(status_code=422, detail="Discount cannot exceed the subtotal")
    taxable_value = round(subtotal - discount, 2)
    # Invoice-level discount reduces each line's taxable value proportionally before GST.
    taxable_ratio = taxable_value / subtotal if subtotal else 0
    for item in invoice.items:
        item.tax_amount = round(item.amount * taxable_ratio * item.gst_percentage / 100, 2)
    tax = round(sum(item.tax_amount for item in invoice.items), 2)
    intra_state = company.gstin[:2] == _state_code_of_supply(invoice.place_of_supply, customer)
    if intra_state:
        invoice.cgst_amount = round(tax / 2, 2)
        invoice.sgst_amount = round(tax - invoice.cgst_amount, 2)
        invoice.igst_amount = 0
    else:
        invoice.cgst_amount = 0
        invoice.sgst_amount = 0
        invoice.igst_amount = tax
    total_before_rounding = round(taxable_value + tax, 2)
    grand_total = float(Decimal(str(total_before_rounding)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    invoice.subtotal = subtotal
    invoice.discount_amount = discount
    invoice.taxable_value = taxable_value
    invoice.tax_amount = tax
    invoice.round_off = round(grand_total - total_before_rounding, 2)
    invoice.grand_total = grand_total
    invoice.amount_in_words = amount_to_words(grand_total)


def backfill_invoice_totals(db: Session) -> int:
    """Recalculate invoices saved before discount/taxable value/round off were stored."""
    stale = list(db.scalars(_invoice_query().where(InvoiceHeader.taxable_value == 0, InvoiceHeader.subtotal > 0)))
    for invoice in stale:
        _apply_totals(invoice, invoice.company, invoice.customer)
    if stale:
        db.commit()
    return len(stale)


def _next_invoice_no(db: Session, invoice_date: date) -> str:
    prefix = f"INV-{invoice_date:%Y%m}-"
    existing = db.scalars(select(InvoiceHeader.invoice_no).where(InvoiceHeader.invoice_no.like(f"{prefix}%"))).all()
    sequence = max((int(no[len(prefix):]) for no in existing if no[len(prefix):].isdigit()), default=0) + 1
    return f"{prefix}{sequence:04d}"


def _ensure_unique_invoice_no(db: Session, invoice_no: str, exclude_id: int | None = None) -> None:
    query = select(InvoiceHeader.invoice_id).where(InvoiceHeader.invoice_no == invoice_no)
    if exclude_id is not None:
        query = query.where(InvoiceHeader.invoice_id != exclude_id)
    if db.scalar(query) is not None:
        raise HTTPException(status_code=409, detail=f"Invoice number {invoice_no} already exists")


def _invoice_query():
    return select(InvoiceHeader).options(
        selectinload(InvoiceHeader.company),
        selectinload(InvoiceHeader.customer),
        selectinload(InvoiceHeader.items),
    )


def list_invoices(db: Session, search: str | None = None) -> list[dict]:
    query = (
        select(InvoiceHeader)
        .join(InvoiceHeader.company)
        .join(InvoiceHeader.customer)
        .options(selectinload(InvoiceHeader.company), selectinload(InvoiceHeader.customer))
        .order_by(InvoiceHeader.invoice_date.desc(), InvoiceHeader.invoice_id.desc())
    )
    condition = _search_filter(
        [
            InvoiceHeader.invoice_no,
            InvoiceHeader.po_reference,
            CompanyMaster.company_name,
            InvoiceCustomerMaster.customer_name,
        ],
        search,
    )
    if condition is not None:
        query = query.where(condition)
    return [
        {
            "invoice_id": invoice.invoice_id,
            "invoice_no": invoice.invoice_no,
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "po_reference": invoice.po_reference,
            "place_of_supply": invoice.place_of_supply,
            "company_id": invoice.company_id,
            "customer_id": invoice.customer_id,
            "company_name": invoice.company.company_name,
            "customer_name": invoice.customer.customer_name,
            "payment_terms": invoice.payment_terms,
            "source": invoice.source,
            "subtotal": invoice.subtotal,
            "tax_amount": invoice.tax_amount,
            "grand_total": invoice.grand_total,
        }
        for invoice in db.scalars(query)
    ]


def get_invoice(db: Session, invoice_id: int) -> InvoiceHeader:
    invoice = db.scalar(_invoice_query().where(InvoiceHeader.invoice_id == invoice_id))
    if invoice is None:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} was not found")
    return invoice


def _header_values(payload: InvoiceInput) -> dict:
    return {
        "invoice_date": payload.invoice_date,
        "due_date": payload.due_date,
        "po_reference": (payload.po_reference or "").strip() or None,
        "place_of_supply": payload.place_of_supply.strip(),
        "company_id": payload.company_id,
        "customer_id": payload.customer_id,
        "payment_terms": (payload.payment_terms or "").strip() or None,
        "terms_and_conditions": (payload.terms_and_conditions or "").strip() or None,
        "discount_amount": payload.discount_amount,
    }


def create_invoice(db: Session, payload: InvoiceCreate) -> InvoiceHeader:
    company = get_company(db, payload.company_id)
    customer = get_customer(db, payload.customer_id)
    invoice_no = (payload.invoice_no or "").strip() or _next_invoice_no(db, payload.invoice_date)
    _ensure_unique_invoice_no(db, invoice_no)
    invoice = InvoiceHeader(invoice_no=invoice_no, source=payload.source, **_header_values(payload))
    invoice.items = _build_items(db, payload)
    _apply_totals(invoice, company, customer)
    db.add(invoice)
    db.commit()
    return get_invoice(db, invoice.invoice_id)


def update_invoice(db: Session, invoice_id: int, payload: InvoiceInput) -> InvoiceHeader:
    invoice = get_invoice(db, invoice_id)
    company = get_company(db, payload.company_id)
    customer = get_customer(db, payload.customer_id)
    invoice_no = (payload.invoice_no or "").strip() or invoice.invoice_no
    _ensure_unique_invoice_no(db, invoice_no, exclude_id=invoice_id)
    invoice.invoice_no = invoice_no
    _apply(invoice, _header_values(payload))
    invoice.items = _build_items(db, payload)
    _apply_totals(invoice, company, customer)
    db.commit()
    db.expire_all()
    return get_invoice(db, invoice_id)


def delete_invoice(db: Session, invoice_id: int) -> None:
    invoice = get_invoice(db, invoice_id)
    db.delete(invoice)
    db.commit()
