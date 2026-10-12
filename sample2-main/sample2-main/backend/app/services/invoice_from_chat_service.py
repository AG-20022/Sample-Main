"""Placeholder for building invoice drafts from chat conversations.

Future implementation: extract invoice intent and line items from the chat transcript,
resolve them against the company/customer/product masters, and return an
``InvoiceCreate`` draft with ``source="chat"`` for user review before saving.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.schemas.invoice_management import InvoiceDraftResponse, InvoiceFromChatRequest


def build_invoice_draft_from_chat(db: Session, request: InvoiceFromChatRequest) -> InvoiceDraftResponse:
    return InvoiceDraftResponse(
        status="not_implemented",
        source="chat",
        message="Invoice extraction from chat requests is not implemented yet.",
        draft=None,
    )
