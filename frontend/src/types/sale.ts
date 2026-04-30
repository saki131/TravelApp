export interface SaleEvent {
  id: string;
  category: "flight" | "hotel" | "package";
  title: string;
  description?: string;
  sale_start?: string;
  sale_end?: string;
  travel_start?: string;
  travel_end?: string;
  discount_rate?: number;
  min_price_jpy?: number;
  target_routes?: { origin: string; destination: string }[];
  target_destinations?: string[];
  coupon_code?: string;
  booking_url?: string;
  source: string;
  is_verified: boolean;
  created_at: string;
}

export interface SaleListResponse {
  total: number;
  items: SaleEvent[];
}
