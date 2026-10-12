import axios, { AxiosError, AxiosInstance } from 'axios';
import { createContext, useContext } from 'react';

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? (window.location.port === '5173' ? 'http://localhost:8000' : window.location.origin);

export type Company = {
  company_id: number;
  company_name: string;
  gstin: string;
  pan: string;
  phone: string | null;
  email: string | null;
  address: string;
  ship_from_address: string | null;
  bank_name: string | null;
  bank_account_name: string | null;
  bank_account_no: string | null;
  bank_ifsc: string | null;
  bank_branch: string | null;
};

export type Customer = {
  customer_id: number;
  customer_name: string;
  gstin: string | null;
  contact_person: string | null;
  phone: string | null;
  email: string | null;
  billing_address: string;
  shipping_address: string | null;
  state_code: string;
};

export type Product = {
  product_id: number;
  product_name: string;
  hsn_sac: string;
  unit: string;
  rate: number;
  gst_percentage: number;
};

export type InvoiceItemInput = {
  product_id: number;
  description: string;
  hsn_sac: string;
  quantity: number;
  unit: string;
  rate: number;
  gst_percentage: number;
};

export type InvoiceItem = InvoiceItemInput & {
  item_id: number;
  line_no: number;
  amount: number;
  tax_amount: number;
};

export type InvoiceInput = {
  invoice_no: string;
  invoice_date: string;
  due_date: string | null;
  po_reference: string;
  place_of_supply: string;
  company_id: number;
  customer_id: number;
  payment_terms: string;
  terms_and_conditions: string;
  discount_amount: number;
  items: InvoiceItemInput[];
};

export type InvoiceSummary = {
  invoice_id: number;
  invoice_no: string;
  invoice_date: string;
  due_date: string | null;
  po_reference: string | null;
  place_of_supply: string;
  company_name: string;
  customer_name: string;
  source: string;
  subtotal: number;
  tax_amount: number;
  grand_total: number;
};

export type Invoice = {
  invoice_id: number;
  invoice_no: string;
  invoice_date: string;
  due_date: string | null;
  po_reference: string | null;
  place_of_supply: string;
  company_id: number;
  customer_id: number;
  payment_terms: string | null;
  terms_and_conditions: string | null;
  source: string;
  subtotal: number;
  discount_amount: number;
  taxable_value: number;
  cgst_amount: number;
  sgst_amount: number;
  igst_amount: number;
  tax_amount: number;
  round_off: number;
  grand_total: number;
  amount_in_words: string;
  company: Company;
  customer: Customer;
  items: InvoiceItem[];
};

export type MasterResource = 'companies' | 'customers' | 'products';

export function createInvoiceApi(accessToken: string): AxiosInstance {
  return axios.create({
    baseURL: `${API_BASE}/api/invoice-management`,
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export const InvoiceApiContext = createContext<AxiosInstance | null>(null);

export function useInvoiceApi(): AxiosInstance {
  const api = useContext(InvoiceApiContext);
  if (!api) throw new Error('useInvoiceApi must be used inside InvoiceModule');
  return api;
}

type ErrorDetail = string | { msg: string; loc?: (string | number)[] }[];

export function getErrorMessage(error: unknown, fallback = 'Request failed.'): string {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as { detail?: ErrorDetail } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg.replace(/^Value error, /, '')).join('; ');
    }
    return error.message || fallback;
  }
  return error instanceof Error ? error.message : fallback;
}
