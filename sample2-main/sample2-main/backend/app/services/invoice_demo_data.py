from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import CompanyMaster, InvoiceCustomerMaster, InvoiceHeader, ProductCatalog
from backend.app.schemas.invoice_management import CompanyInput, CustomerInput, InvoiceCreate, ProductInput
from backend.app.services import invoice_management_service as service

DEMO_COMPANIES = [
    {
        "company_name": "Wipro Medical Devices Pvt Ltd", "gstin": "29AABCW1234K1Z5", "pan": "AABCW1234K",
        "phone": "+91 80 4110 2000", "email": "billing@wipro-meddevices.example",
        "address": "Doddakannelli, Sarjapur Road\nBengaluru, Karnataka 560035",
        "ship_from_address": "Warehouse 4, Electronic City Phase II\nBengaluru, Karnataka 560100",
        "bank_name": "State Bank of India", "bank_account_name": "Wipro Medical Devices Pvt Ltd",
        "bank_account_no": "38291045672", "bank_ifsc": "SBIN0040011",
        "bank_branch": "Koramangala, Bengaluru",
    },
    {
        "company_name": "Acme Healthcare Solutions LLP", "gstin": "27AAFCA5678M1Z2", "pan": "AAFCA5678M",
        "phone": "+91 22 6650 3300", "email": "accounts@acmehealth.example",
        "address": "Unit 12, Hiranandani Business Park, Powai\nMumbai, Maharashtra 400076",
        "ship_from_address": "Plot 7, MIDC Bhosari\nPune, Maharashtra 411026",
        "bank_name": "HDFC Bank", "bank_account_name": "Acme Healthcare Solutions LLP",
        "bank_account_no": "50200012345678", "bank_ifsc": "HDFC0000212",
        "bank_branch": "Powai, Mumbai",
    },
    {
        "company_name": "Contoso MedTech India Pvt Ltd", "gstin": "07AAGCC3456H1Z4", "pan": "AAGCC3456H",
        "phone": "+91 11 4060 7000", "email": "finance@contoso-medtech.example",
        "address": "9th Floor, DLF Centre, Sansad Marg\nNew Delhi, Delhi 110001",
        "ship_from_address": "Khasra 112, Mundka Industrial Area\nNew Delhi, Delhi 110041",
        "bank_name": "ICICI Bank", "bank_account_name": "Contoso MedTech India Pvt Ltd",
        "bank_account_no": "000405112233", "bank_ifsc": "ICIC0000004", "bank_branch": "Connaught Place, New Delhi",
    },
    {
        "company_name": "Northwind Surgical Supplies", "gstin": "24AAJFN7890L1Z6", "pan": "AAJFN7890L",
        "phone": "+91 79 2656 4400", "email": "sales@northwind-surgical.example",
        "address": "302 Shapath Hexa, S.G. Highway\nAhmedabad, Gujarat 380060",
        "ship_from_address": "Shed 18, Changodar GIDC\nAhmedabad, Gujarat 382213",
        "bank_name": "Axis Bank", "bank_account_name": "Northwind Surgical Supplies",
        "bank_account_no": "921020045678901", "bank_ifsc": "UTIB0000080", "bank_branch": "Navrangpura, Ahmedabad",
    },
]

DEMO_CUSTOMERS = [
    {
        "customer_name": "Northstar Hospitals Pvt Ltd", "gstin": "29AACCN4321P1Z8", "contact_person": "Dr. Kavya Rao",
        "phone": "+91 80 2222 7788", "email": "procurement@northstar.example",
        "billing_address": "14 Residency Road\nBengaluru, Karnataka 560025",
        "shipping_address": "Northstar Hospital Stores, Whitefield\nBengaluru, Karnataka 560066", "state_code": "29",
    },
    {
        "customer_name": "Contoso Diagnostics", "gstin": "27AADCC8765Q1Z3", "contact_person": "Rahul Mehta",
        "phone": "+91 20 4567 1234", "email": "ap@contoso-diag.example",
        "billing_address": "5th Floor, Baner Business Bay\nPune, Maharashtra 411045", "shipping_address": None,
        "state_code": "27",
    },
    {
        "customer_name": "Apollo Clinic Chennai", "gstin": "33AAECA2468R1Z9", "contact_person": "S. Lakshmi",
        "phone": "+91 44 2811 0000", "email": "purchase@apolloclinic.example",
        "billing_address": "21 Greams Lane\nChennai, Tamil Nadu 600006",
        "shipping_address": "Central Stores, Guindy Industrial Estate\nChennai, Tamil Nadu 600032", "state_code": "33",
    },
    {
        "customer_name": "City Care Pharmacy", "gstin": None, "contact_person": "Amit Verma",
        "phone": "+91 11 4155 9090", "email": "citycare@pharmacy.example",
        "billing_address": "B-42 Lajpat Nagar II\nNew Delhi, Delhi 110024", "shipping_address": None, "state_code": "07",
    },
    {
        "customer_name": "Fortis Care Hyderabad", "gstin": "36AABCF1122G1Z7", "contact_person": "Dr. Ravi Teja",
        "phone": "+91 40 6644 1000", "email": "stores@fortiscare.example",
        "billing_address": "Road No. 12, Banjara Hills\nHyderabad, Telangana 500034", "shipping_address": None,
        "state_code": "36",
    },
    {
        "customer_name": "Kolkata Heart Institute", "gstin": "19AAATK3344J1Z1", "contact_person": "Ananya Sen",
        "phone": "+91 33 4011 2200", "email": "purchase@kolkataheart.example",
        "billing_address": "58 Park Street\nKolkata, West Bengal 700016",
        "shipping_address": "Gate 3 Receiving Bay, Salt Lake Sector V\nKolkata, West Bengal 700091", "state_code": "19",
    },
    {
        "customer_name": "Lucknow Diagnostics Centre", "gstin": "09AAFCL5566N1Z3", "contact_person": "Vikas Srivastava",
        "phone": "+91 522 400 8800", "email": "admin@lucknowdiag.example",
        "billing_address": "14 Hazratganj\nLucknow, Uttar Pradesh 226001", "shipping_address": None, "state_code": "09",
    },
    {
        "customer_name": "Kochi Medical College Hospital", "gstin": "32AAATK7788P1Z5", "contact_person": "Dr. Meera Nair",
        "phone": "+91 484 270 5500", "email": "cmo@kochimch.example",
        "billing_address": "Kalamassery\nKochi, Kerala 683503", "shipping_address": None, "state_code": "32",
    },
    {
        "customer_name": "Sunrise Nursing Home", "gstin": "24ABDFS9900Q1Z2", "contact_person": "Hetal Patel",
        "phone": "+91 79 2747 3300", "email": "accounts@sunrisenh.example",
        "billing_address": "Near Law Garden, Ellis Bridge\nAhmedabad, Gujarat 380006", "shipping_address": None,
        "state_code": "24",
    },
    {
        "customer_name": "MedPlus Pharmacy Delhi", "gstin": "07AAKCM2233R1Z8", "contact_person": "Rohit Khanna",
        "phone": "+91 11 4700 1212", "email": "delhi@medplus.example",
        "billing_address": "F-21 Rajouri Garden Main Market\nNew Delhi, Delhi 110027",
        "shipping_address": "MedPlus DC, Okhla Phase II\nNew Delhi, Delhi 110020", "state_code": "07",
    },
]

DEMO_PRODUCTS = [
    {"product_name": "Surgical Gloves (Box of 100)", "hsn_sac": "4015", "unit": "Box", "rate": 450, "gst_percentage": 12},
    {"product_name": "Digital Thermometer", "hsn_sac": "9025", "unit": "Nos", "rate": 350, "gst_percentage": 18},
    {"product_name": "Pulse Oximeter", "hsn_sac": "9018", "unit": "Nos", "rate": 1850, "gst_percentage": 12},
    {"product_name": "Disposable Syringe 5ml (Pack of 100)", "hsn_sac": "9018", "unit": "Pack", "rate": 620, "gst_percentage": 12},
    {"product_name": "Annual Maintenance Service", "hsn_sac": "998719", "unit": "Year", "rate": 25000, "gst_percentage": 18},
    {"product_name": "Equipment Installation", "hsn_sac": "998729", "unit": "Hrs", "rate": 1200, "gst_percentage": 18},
    {"product_name": "Surgical Face Mask (Box of 50)", "hsn_sac": "6307", "unit": "Box", "rate": 187.5, "gst_percentage": 5},
    {"product_name": "N95 Respirator", "hsn_sac": "6307", "unit": "Nos", "rate": 89.75, "gst_percentage": 5},
    {"product_name": "Blood Pressure Monitor", "hsn_sac": "9018", "unit": "Nos", "rate": 2349, "gst_percentage": 12},
    {"product_name": "Glucometer Kit", "hsn_sac": "9027", "unit": "Kit", "rate": 1249.5, "gst_percentage": 12},
    {"product_name": "IV Cannula 20G (Pack of 50)", "hsn_sac": "9018", "unit": "Pack", "rate": 1475, "gst_percentage": 12},
    {"product_name": "Hospital Bed Mattress", "hsn_sac": "9404", "unit": "Nos", "rate": 8650, "gst_percentage": 18},
    {"product_name": "Foldable Wheelchair", "hsn_sac": "8713", "unit": "Nos", "rate": 6499, "gst_percentage": 5},
    {"product_name": "Calibration Service", "hsn_sac": "998346", "unit": "Visit", "rate": 3500, "gst_percentage": 18},
    {"product_name": "Staff Training Session", "hsn_sac": "999293", "unit": "Hrs", "rate": 2750, "gst_percentage": 18},
]

PAYMENT_TERMS = {
    15: "Net 15 days from invoice date.",
    30: "Net 30 days from invoice date.",
    45: "Net 45 days from invoice date.",
}

# (invoice no, company, customer, place of supply, days before today, PO, discount, credit days, [(product, qty)])
DEMO_INVOICES = [
    ("WMD/26-27/0001", 0, 0, "29-Karnataka", 85, "PO-NSH-0988", 2500, 30, [(0, 60), (2, 12), (4, 1)]),
    ("WMD/26-27/0002", 0, 2, "33-Tamil Nadu", 64, "PO-APC-7781", 0, 45, [(1, 25), (3, 15), (9, 10)]),
    ("WMD/26-27/0003", 0, 4, "36-Telangana", 41, "PO-FCH-2210", 1250.75, 30, [(8, 8), (10, 20), (6, 40)]),
    ("WMD/26-27/0004", 0, 7, "32-Kerala", 18, "PO-KMC-0451", 0, 15, [(11, 4), (12, 3), (14, 6)]),
    ("WMD/26-27/0005", 0, 0, "29-Karnataka", 3, "PO-NSH-1042", 999.5, 30, [(7, 120), (9, 15), (13, 2)]),
    ("AHS/26-27/0001", 1, 1, "27-Maharashtra", 77, "PO-CTD-0193", 500, 30, [(2, 6), (5, 8)]),
    ("AHS/26-27/0002", 1, 3, "07-Delhi", 52, None, 0, 15, [(0, 10), (1, 12), (3, 5), (6, 25)]),
    ("AHS/26-27/0003", 1, 5, "19-West Bengal", 27, "PO-KHI-3390", 3000, 45, [(4, 1), (13, 3), (8, 10)]),
    ("AHS/26-27/0004", 1, 1, "27-Maharashtra", 9, "PO-CTD-0247", 0, 30, [(9, 30), (7, 200)]),
    ("CMT/26-27/0001", 2, 9, "07-Delhi", 70, "PO-MPD-5521", 0, 15, [(6, 100), (7, 300), (1, 40)]),
    ("CMT/26-27/0002", 2, 6, "09-Uttar Pradesh", 35, "PO-LDC-0112", 1800, 30, [(8, 6), (9, 12), (14, 4)]),
    ("CMT/26-27/0003", 2, 3, "07-Delhi", 6, None, 250, 15, [(0, 15), (3, 20), (10, 5)]),
    ("NWS/26-27/0001", 3, 8, "24-Gujarat", 58, "PO-SNH-0074", 5000, 45, [(11, 10), (12, 4), (5, 6)]),
    ("NWS/26-27/0002", 3, 1, "27-Maharashtra", 22, "PO-CTD-0231", 0, 30, [(12, 6), (0, 25)]),
    ("NWS/26-27/0003", 3, 4, "36-Telangana", 1, "PO-FCH-2296", 750, 30, [(10, 12), (2, 8), (13, 1)]),
]


def _find(db: Session, column, value):
    return db.scalar(select(column.class_).where(column == value))


def seed_invoice_demo_data(db: Session) -> int:
    """Add any demo companies, customers, products and invoices that are not already present."""
    created = 0

    def ensure(column, key: str, item: dict, create, schema):
        nonlocal created
        record = _find(db, column, item[key])
        if record is None:
            record = create(db, schema(**item))
            created += 1
        return record

    companies = [ensure(CompanyMaster.gstin, "gstin", item, service.create_company, CompanyInput) for item in DEMO_COMPANIES]
    customers = [
        ensure(InvoiceCustomerMaster.customer_name, "customer_name", item, service.create_customer, CustomerInput)
        for item in DEMO_CUSTOMERS
    ]
    products = [
        ensure(ProductCatalog.product_name, "product_name", item, service.create_product, ProductInput)
        for item in DEMO_PRODUCTS
    ]

    today = date.today()
    for invoice_no, company, customer, place, days_ago, po, discount, credit_days, lines in DEMO_INVOICES:
        if _find(db, InvoiceHeader.invoice_no, invoice_no) is not None:
            continue
        invoice_date = today - timedelta(days=days_ago)
        service.create_invoice(db, InvoiceCreate(
            invoice_no=invoice_no,
            invoice_date=invoice_date,
            due_date=invoice_date + timedelta(days=credit_days),
            po_reference=po,
            place_of_supply=place,
            company_id=companies[company].company_id,
            customer_id=customers[customer].customer_id,
            payment_terms=PAYMENT_TERMS[credit_days],
            discount_amount=discount,
            items=[{"product_id": products[product].product_id, "quantity": qty} for product, qty in lines],
        ))
        created += 1
    return created
