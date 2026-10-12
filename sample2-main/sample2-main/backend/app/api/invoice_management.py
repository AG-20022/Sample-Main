from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import User
from backend.app.schemas.invoice_management import (
    CompanyInput,
    CompanyRead,
    CustomerInput,
    CustomerRead,
    InvoiceCreate,
    InvoiceDraftResponse,
    InvoiceFromChatRequest,
    InvoiceFromEmailRequest,
    InvoiceRead,
    InvoiceSummary,
    InvoiceUpdate,
    ProductInput,
    ProductRead,
)
from backend.app.services import invoice_management_service as service
from backend.app.services.auth_service import decode_access_token
from backend.app.services.invoice_from_chat_service import build_invoice_draft_from_chat
from backend.app.services.invoice_from_email_service import build_invoice_draft_from_email


def get_authenticated_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> User:
    scheme, _, token = authorization.partition(" ")
    claims = decode_access_token(token) if scheme.lower() == "bearer" else None
    user = db.get(User, claims.get("sub")) if claims else None
    if user is None or user.email != claims.get("email"):
        raise HTTPException(status_code=401, detail="Sign in to manage invoices")
    return user


# Prefixed separately from /api/invoices, which serves order-based invoice creation.
router = APIRouter(
    prefix="/api/invoice-management",
    tags=["invoice-management"],
    dependencies=[Depends(get_authenticated_user)],
)

SearchQuery = Query(default=None, max_length=100)


# ---------- Company Master ----------


@router.get("/companies", response_model=list[CompanyRead])
def get_companies(search: str | None = SearchQuery, db: Session = Depends(get_db)):
    return service.list_companies(db, search)


@router.post("/companies", response_model=CompanyRead, status_code=201)
def post_company(payload: CompanyInput, db: Session = Depends(get_db)):
    return service.create_company(db, payload)


@router.get("/companies/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)):
    return service.get_company(db, company_id)


@router.put("/companies/{company_id}", response_model=CompanyRead)
def put_company(company_id: int, payload: CompanyInput, db: Session = Depends(get_db)):
    return service.update_company(db, company_id, payload)


@router.delete("/companies/{company_id}", status_code=204)
def remove_company(company_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_company(db, company_id)
    return Response(status_code=204)


# ---------- Customer Master ----------


@router.get("/customers", response_model=list[CustomerRead])
def get_customers(search: str | None = SearchQuery, db: Session = Depends(get_db)):
    return service.list_customers(db, search)


@router.post("/customers", response_model=CustomerRead, status_code=201)
def post_customer(payload: CustomerInput, db: Session = Depends(get_db)):
    return service.create_customer(db, payload)


@router.get("/customers/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return service.get_customer(db, customer_id)


@router.put("/customers/{customer_id}", response_model=CustomerRead)
def put_customer(customer_id: int, payload: CustomerInput, db: Session = Depends(get_db)):
    return service.update_customer(db, customer_id, payload)


@router.delete("/customers/{customer_id}", status_code=204)
def remove_customer(customer_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_customer(db, customer_id)
    return Response(status_code=204)


# ---------- Product Catalog ----------


@router.get("/products", response_model=list[ProductRead])
def get_products(search: str | None = SearchQuery, db: Session = Depends(get_db)):
    return service.list_products(db, search)


@router.post("/products", response_model=ProductRead, status_code=201)
def post_product(payload: ProductInput, db: Session = Depends(get_db)):
    return service.create_product(db, payload)


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return service.get_product(db, product_id)


@router.put("/products/{product_id}", response_model=ProductRead)
def put_product(product_id: int, payload: ProductInput, db: Session = Depends(get_db)):
    return service.update_product(db, product_id, payload)


@router.delete("/products/{product_id}", status_code=204)
def remove_product(product_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_product(db, product_id)
    return Response(status_code=204)


# ---------- Invoices ----------


@router.get("/invoices", response_model=list[InvoiceSummary])
def get_invoices(search: str | None = SearchQuery, db: Session = Depends(get_db)):
    return service.list_invoices(db, search)


@router.post("/invoices", response_model=InvoiceRead, status_code=201)
def post_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    return service.create_invoice(db, payload)


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    return service.get_invoice(db, invoice_id)


@router.put("/invoices/{invoice_id}", response_model=InvoiceRead)
def put_invoice(invoice_id: int, payload: InvoiceUpdate, db: Session = Depends(get_db)):
    return service.update_invoice(db, invoice_id, payload)


@router.delete("/invoices/{invoice_id}", status_code=204)
def remove_invoice(invoice_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_invoice(db, invoice_id)
    return Response(status_code=204)


# ---------- Future integration hooks ----------


@router.post("/invoices/from-email", response_model=InvoiceDraftResponse)
def invoice_from_email(payload: InvoiceFromEmailRequest, db: Session = Depends(get_db)):
    return build_invoice_draft_from_email(db, payload)


@router.post("/invoices/from-chat", response_model=InvoiceDraftResponse)
def invoice_from_chat(payload: InvoiceFromChatRequest, db: Session = Depends(get_db)):
    return build_invoice_draft_from_chat(db, payload)
