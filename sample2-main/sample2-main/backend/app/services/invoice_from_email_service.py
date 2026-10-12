"""Placeholder for building invoice drafts from inbound email requests.

Future implementation: parse the email (e.g. via the RAG/LLM pipeline), resolve the
company, customer and products against the masters, and return an ``InvoiceCreate``
draft with ``source="email"`` for user review before saving.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.schemas.invoice_management import InvoiceDraftResponse, InvoiceFromEmailRequest


def build_invoice_draft_from_email(db: Session, request: InvoiceFromEmailRequest) -> InvoiceDraftResponse:
    return InvoiceDraftResponse(
        status="not_implemented",
        source="email",
        message="Invoice extraction from email requests is not implemented yet.",
        draft=None,
    )
