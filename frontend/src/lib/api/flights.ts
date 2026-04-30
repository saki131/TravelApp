import { apiFetch } from "./client";
import type {
  FlightSearchParams,
  FlightSearchResponse,
  PriceCalendarResponse,
  InspireResponse,
} from "@/types/flight";

export const flightApi = {
  search: (params: FlightSearchParams) =>
    apiFetch<FlightSearchResponse>("/flights/search", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  priceCalendar: (origin: string, destination: string, year: number, month: number) =>
    apiFetch<PriceCalendarResponse>(
      `/flights/price-calendar?origin=${origin}&destination=${destination}&year=${year}&month=${month}`
    ),

  inspire: (
    origin: string,
    dateFrom: string,
    dateTo: string,
    maxPrice?: number
  ) => {
    const params = new URLSearchParams({
      origin,
      date_from: dateFrom,
      date_to:   dateTo,
    });
    if (maxPrice) params.set("max_price", String(maxPrice));
    return apiFetch<InspireResponse>(`/flights/inspire?${params}`);
  },

  suggestAirports: (q: string) =>
    apiFetch<{ iata_code: string; name_ja: string; city_ja: string }[]>(
      `/airports/suggest?q=${encodeURIComponent(q)}`
    ),
};
