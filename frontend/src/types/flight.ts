export interface FlightItinerary {
  id: string;
  departure_iata: string;
  arrival_iata: string;
  departure_time: string;
  arrival_time: string;
  duration_minutes: number;
  stops: number;
  airline_code: string;
  airline_name?: string;
  flight_numbers: string[];
  price_jpy: number;
  booking_url?: string;
  source_site: string;
}

export interface FlightSearchResponse {
  origin: string;
  destination: string;
  departure_date: string;
  results: FlightItinerary[];
  cached: boolean;
  cached_at?: string;
}

export interface PriceCalendarItem {
  date: string;
  price_jpy: number | null;
}

export interface PriceCalendarResponse {
  origin: string;
  destination: string;
  prices: PriceCalendarItem[];
}

export interface InspireDestination {
  destination_iata: string;
  destination_name?: string;
  country_code?: string;
  min_price_jpy: number;
  cheapest_date?: string;
  duration_days?: number;
}

export interface InspireResponse {
  origin: string;
  destinations: InspireDestination[];
  cached: boolean;
}

export interface FlightSearchParams {
  origin: string;
  destination: string;
  departure_date: string;
  return_date?: string;
  adults?: number;
  cabin_class?: string;
  nonstop_only?: boolean;
  max_price?: number;
}
