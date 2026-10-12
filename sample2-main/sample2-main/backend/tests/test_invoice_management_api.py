import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import models  # noqa: F401
from backend.app.db.database import Base, get_db
from backend.app.db.models import User
from backend.app.main import app
from backend.app.services.auth_service import create_access_token

COMPANY = {
    "company_name": "Acme Pvt Ltd", "gstin": "29ABCDE1234F1Z5", "pan": "ABCDE1234F", "phone": "+91 80 1234 5678",
    "email": "billing@acme.test", "address": "MG Road, Bengaluru", "ship_from_address": "Warehouse, Bengaluru",
}
CUSTOMER = {"customer_name": "Buyer Co", "gstin": "27PQRSX5678K1Z2", "billing_address": "Pune", "state_code": "27"}
PRODUCT = {"product_name": "Widget", "hsn_sac": "8471", "unit": "Nos", "rate": 1000, "gst_percentage": 18}


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db:
        user = User(email="tester@local.dev", name="Tester", password_hash="x")
        db.add(user)
        db.commit()
        token = create_access_token(user.id, user.email, "tester")

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    test_client.headers["Authorization"] = f"Bearer {token}"
    yield test_client
    app.dependency_overrides.pop(get_db, None)


def test_requires_authentication(client):
    response = client.get("/api/invoice-management/invoices", headers={"Authorization": ""})
    assert response.status_code == 401


def test_master_crud_and_search(client):
    company = client.post("/api/invoice-management/companies", json=COMPANY)
    assert company.status_code == 201
    company_id = company.json()["company_id"]

    assert client.post("/api/invoice-management/companies", json=COMPANY).status_code == 409
    assert [c["company_id"] for c in client.get("/api/invoice-management/companies", params={"search": "acme"}).json()] == [company_id]
    assert client.get("/api/invoice-management/companies", params={"search": "nomatch"}).json() == []

    updated = client.put(f"/api/invoice-management/companies/{company_id}", json={**COMPANY, "company_name": "Acme Renamed"})
    assert updated.json()["company_name"] == "Acme Renamed"
    assert client.get(f"/api/invoice-management/companies/{company_id}").json()["company_name"] == "Acme Renamed"
    assert client.delete(f"/api/invoice-management/companies/{company_id}").status_code == 204
    assert client.get(f"/api/invoice-management/companies/{company_id}").status_code == 404


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("companies", {**COMPANY, "gstin": "BADGSTIN"}),
        ("companies", {**COMPANY, "pan": "ZZZZZ9999Z"}),
        ("companies", {**COMPANY, "email": "not-an-email"}),
        ("customers", {**CUSTOMER, "state_code": "29"}),
        ("products", {**PRODUCT, "hsn_sac": "12"}),
        ("products", {**PRODUCT, "gst_percentage": 120}),
    ],
)
def test_master_validation_errors(client, path, payload):
    assert client.post(f"/api/invoice-management/{path}", json=payload).status_code == 422


def test_invoice_lifecycle_with_tax_calculation(client):
    company_id = client.post("/api/invoice-management/companies", json=COMPANY).json()["company_id"]
    customer_id = client.post("/api/invoice-management/customers", json=CUSTOMER).json()["customer_id"]
    product_id = client.post("/api/invoice-management/products", json=PRODUCT).json()["product_id"]
    invoice_payload = {
        "invoice_date": "2026-10-12", "due_date": "2026-11-11", "po_reference": "PO-77", "place_of_supply": "27-Maharashtra",
        "company_id": company_id, "customer_id": customer_id, "payment_terms": "Net 30",
        "items": [{"product_id": product_id, "quantity": 3}],
    }

    created = client.post("/api/invoice-management/invoices", json=invoice_payload)
    assert created.status_code == 201
    invoice = created.json()
    assert invoice["invoice_no"] == "INV-202610-0001"
    assert invoice["items"][0]["description"] == "Widget"
    assert (invoice["subtotal"], invoice["igst_amount"], invoice["cgst_amount"], invoice["grand_total"]) == (3000, 540, 0, 3540)
    assert invoice["amount_in_words"] == "Indian Rupees Three Thousand Five Hundred Forty Only"
    assert invoice["company"]["gstin"] == COMPANY["gstin"]

    listed = client.get("/api/invoice-management/invoices", params={"search": "Buyer"}).json()
    assert [row["invoice_id"] for row in listed] == [invoice["invoice_id"]]

    intra_state = {**invoice_payload, "invoice_no": invoice["invoice_no"], "place_of_supply": "29-Karnataka",
                   "items": [{"product_id": product_id, "quantity": 1, "rate": 500}, {"product_id": product_id, "quantity": 2}]}
    updated = client.put(f"/api/invoice-management/invoices/{invoice['invoice_id']}", json=intra_state).json()
    assert len(updated["items"]) == 2
    assert (updated["subtotal"], updated["cgst_amount"], updated["sgst_amount"], updated["igst_amount"]) == (2500, 225, 225, 0)

    assert client.delete(f"/api/invoice-management/products/{product_id}").status_code == 409
    assert client.delete(f"/api/invoice-management/invoices/{invoice['invoice_id']}").status_code == 204
    assert client.get(f"/api/invoice-management/invoices/{invoice['invoice_id']}").status_code == 404
    assert client.delete(f"/api/invoice-management/products/{product_id}").status_code == 204


def test_invoice_validation_errors(client):
    base = {"invoice_date": "2026-10-12", "place_of_supply": "29", "company_id": 1, "customer_id": 1}
    assert client.post("/api/invoice-management/invoices", json={**base, "items": []}).status_code == 422
    assert client.post("/api/invoice-management/invoices", json={**base, "due_date": "2026-10-01", "items": [{"product_id": 1, "quantity": 1}]}).status_code == 422
    assert client.post("/api/invoice-management/invoices", json={**base, "items": [{"product_id": 1, "quantity": 0}]}).status_code == 422
    assert client.post("/api/invoice-management/invoices", json={**base, "items": [{"product_id": 1, "quantity": 1}]}).status_code == 404


def test_integration_hooks_return_placeholder(client):
    email = client.post("/api/invoice-management/invoices/from-email", json={"sender": "a@b.c", "body": "Please invoice"})
    chat = client.post("/api/invoice-management/invoices/from-chat", json={"messages": ["Invoice 3 widgets"]})
    assert email.json()["status"] == chat.json()["status"] == "not_implemented"


def test_invoice_spa_routes_are_served(client):
    for path in ["/invoices", "/invoices/create", "/invoices/5", "/invoices/5/edit", "/company-master", "/customer-master", "/product-catalog"]:
        assert client.get(path, follow_redirects=False).status_code in {200, 307}
