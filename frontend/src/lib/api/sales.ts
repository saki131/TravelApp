import { apiFetch } from "./client";
import type { SaleListResponse, SaleEvent } from "@/types/sale";

export const saleApi = {
  list: (params?: { category?: string; date_from?: string; date_to?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.category)  qs.set("category",  params.category);
    if (params?.date_from) qs.set("date_from",  params.date_from);
    if (params?.date_to)   qs.set("date_to",    params.date_to);
    if (params?.limit)     qs.set("limit",       String(params.limit));
    return apiFetch<SaleListResponse>(`/sales?${qs}`);
  },

  today: () => apiFetch<SaleListResponse>("/sales/today"),

  get: (id: string) => apiFetch<SaleEvent>(`/sales/${id}`),
};
