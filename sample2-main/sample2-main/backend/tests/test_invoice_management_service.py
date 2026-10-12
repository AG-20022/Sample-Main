from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from backend.app.db.database import Base, _add_missing_columns
from backend.app.db import models  # noqa: F401
from backend.app.schemas.invoice_management import CompanyInput, CustomerInput, InvoiceCreate, ProductInput
from backend.app.services import invoice_management_service as service


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _seed(db, customer_state="29"):
    company = service.create_company(db, CompanyInput(
        company_name="Acme Pvt Ltd", gstin="29ABCDE1234F1Z5", pan="ABCDE1234F", address="Bengaluru",
    ))
    customer = service.create_customer(db, CustomerInput(
        customer_name="Buyer Co", billing_address="Somewhere", state_code=customer_state,
    ))
    product = service.create_product(db, ProductInput(
        product_name="Widget", hsn_sac="8471", unit="Nos", rate=1000, gst_percentage=18,
    ))
    return company, customer, product


def _invoice(company, customer, product, place="29-Karnataka", **overrides):
    return InvoiceCreate(
        invoice_date=date(2026, 10, 1), place_of_supply=place, company_id=company.company_id,
        customer_id=customer.customer_id, items=[{"product_id": product.product_id, "quantity": 2.5}], **overrides,
    )


def test_amount_to_words_uses_indian_numbering():
    assert service.amount_to_words(1234567.5) == "Indian Rupees Twelve Lakh Thirty Four Thousand Five Hundred Sixty Seven and Fifty Paise Only"
    assert service.amount_to_words(0) == "Indian Rupees Zero Only"


def test_intra_state_invoice_splits_cgst_sgst_and_autofills_lines(db):
    company, customer, product = _seed(db)
    invoice = service.create_invoice(db, _invoice(company, customer, product))

    item = invoice.items[0]
    assert (item.description, item.hsn_sac, item.unit, item.rate, item.gst_percentage) == ("Widget", "8471", "Nos", 1000, 18)
    assert item.amount == 2500
    assert invoice.subtotal == 2500
    assert invoice.cgst_amount == invoice.sgst_amount == 225
    assert invoice.igst_amount == 0
    assert invoice.grand_total == 2950
    assert invoice.invoice_no == "INV-202610-0001"


def test_inter_state_invoice_uses_igst(db):
    company, customer, product = _seed(db, customer_state="27")
    invoice = service.create_invoice(db, _invoice(company, customer, product, place="27-Maharashtra"))
    assert invoice.igst_amount == 450
    assert invoice.cgst_amount == 0


def test_update_replaces_items_and_master_delete_is_blocked(db):
    company, customer, product = _seed(db)
    invoice = service.create_invoice(db, _invoice(company, customer, product, invoice_no="A-1"))
    payload = _invoice(company, customer, product, invoice_no="A-1").model_dump()
    payload["items"] = [{"product_id": product.product_id, "quantity": 1, "rate": 500}]
    updated = service.update_invoice(db, invoice.invoice_id, InvoiceCreate(**payload))
    assert len(updated.items) == 1 and updated.subtotal == 500

    with pytest.raises(HTTPException) as error:
        service.delete_product(db, product.product_id)
    assert error.value.status_code == 409

    service.delete_invoice(db, invoice.invoice_id)
    service.delete_product(db, product.product_id)
    assert service.list_products(db) == []


def test_duplicate_invoice_number_is_rejected(db):
    company, customer, product = _seed(db)
    service.create_invoice(db, _invoice(company, customer, product, invoice_no="DUP"))
    with pytest.raises(HTTPException) as error:
        service.create_invoice(db, _invoice(company, customer, product, invoice_no="DUP"))
    assert error.value.status_code == 409


def test_discount_reduces_taxable_value_and_grand_total_is_rounded(db):
    company, customer, product = _seed(db)
    discounted = service.create_invoice(db, _invoice(company, customer, product, discount_amount=100))
    assert (discounted.subtotal, discounted.discount_amount, discounted.taxable_value) == (2500, 100, 2400)
    assert (discounted.cgst_amount, discounted.sgst_amount, discounted.tax_amount) == (216, 216, 432)
    assert (discounted.round_off, discounted.grand_total) == (0, 2832)

    odd = service.create_product(db, ProductInput(product_name="Odd", hsn_sac="8471", unit="Nos", rate=1000.4, gst_percentage=18))
    rounded = service.create_invoice(db, InvoiceCreate(
        invoice_date=date(2026, 10, 1), place_of_supply="29", company_id=company.company_id,
        customer_id=customer.customer_id, items=[{"product_id": odd.product_id, "quantity": 1}],
    ))
    assert (rounded.taxable_value, rounded.tax_amount, rounded.round_off, rounded.grand_total) == (1000.4, 180.07, -0.47, 1180)
    assert rounded.amount_in_words == "Indian Rupees One Thousand One Hundred Eighty Only"


def test_discount_cannot_exceed_subtotal(db):
    company, customer, product = _seed(db)
    with pytest.raises(HTTPException) as error:
        service.create_invoice(db, _invoice(company, customer, product, discount_amount=5000))
    assert error.value.status_code == 422


def test_missing_columns_are_added_to_existing_tables():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE company_master (company_id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE invoice_header (invoice_id INTEGER PRIMARY KEY, subtotal FLOAT)"))
        connection.execute(text("INSERT INTO invoice_header (invoice_id, subtotal) VALUES (1, 10)"))
    _add_missing_columns(engine, ("company_master", "invoice_header"))
    columns = {column["name"] for column in inspect(engine).get_columns("invoice_header")}
    assert {"discount_amount", "taxable_value", "round_off"} <= columns
    assert "bank_account_name" in {column["name"] for column in inspect(engine).get_columns("company_master")}
    with engine.connect() as connection:
        assert connection.execute(text("SELECT discount_amount, round_off FROM invoice_header")).one() == (0, 0)


def test_demo_data_seeds_valid_records_once(db):
    from backend.app.services.invoice_demo_data import DEMO_INVOICES, seed_invoice_demo_data

    assert seed_invoice_demo_data(db) == 4 + 10 + 15 + len(DEMO_INVOICES)
    assert seed_invoice_demo_data(db) == 0
    assert (len(service.list_companies(db)), len(service.list_customers(db)), len(service.list_products(db))) == (4, 10, 15)
    invoices = [service.get_invoice(db, row["invoice_id"]) for row in service.list_invoices(db)]
    assert len(invoices) == len(DEMO_INVOICES)
    assert all(invoice.grand_total > invoice.taxable_value > 0 for invoice in invoices)
    assert any(invoice.discount_amount > 0 for invoice in invoices)
    assert any(invoice.round_off != 0 for invoice in invoices)
    assert any(invoice.igst_amount > 0 for invoice in invoices) and any(invoice.cgst_amount > 0 for invoice in invoices)
