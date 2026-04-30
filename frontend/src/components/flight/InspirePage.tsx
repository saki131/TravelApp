"use client";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { flightApi } from "@/lib/api/flights";
import { formatPrice } from "@/lib/utils";
import { Search, ArrowRight } from "lucide-react";
import type { InspireDestination } from "@/types/flight";
import AirportInput from "@/components/search/AirportInput";

const BUDGET_OPTIONS = [
  { label: "上限なし", value: 0 },
  { label: "¥20,000以下", value: 20000 },
  { label: "¥30,000以下", value: 30000 },
  { label: "¥50,000以下", value: 50000 },
];

export default function InspirePage() {
  const router = useRouter();
  const sp = useSearchParams();

  const [origin, setOrigin]     = useState(sp.get("origin") ?? "HND");
  const [dateFrom, setDateFrom] = useState(sp.get("date_from") ?? "");
  const [dateTo, setDateTo]     = useState(sp.get("date_to") ?? "");
  const [maxPrice, setMaxPrice] = useState(0);
  const [filter, setFilter]     = useState<"all" | "domestic" | "international">("all");
  const [searching, setSearching] = useState(!!sp.get("origin"));

  const { data, isLoading, error } = useQuery({
    queryKey: ["inspire", origin, dateFrom, dateTo, maxPrice],
    queryFn: () => flightApi.inspire(origin, dateFrom, dateTo, maxPrice || undefined),
    enabled: searching && !!origin && !!dateFrom && !!dateTo,
  });

  const DOMESTIC = ["HND", "NRT", "ITM", "KIX", "OKA", "CTS", "FUK", "NGO", "KOJ"];

  const filtered = (data?.destinations ?? []).filter((d: InspireDestination) => {
    if (filter === "domestic")      return DOMESTIC.includes(d.destination_iata);
    if (filter === "international") return !DOMESTIC.includes(d.destination_iata);
    return true;
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearching(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 検索フォーム */}
      <div className="bg-blue-600 text-white px-4 pt-10 pb-5">
        <h1 className="text-lg font-bold mb-4">✈ どこでも検索</h1>
        <form onSubmit={handleSearch} className="space-y-2">
          <AirportInput
            value={origin}
            onChange={(iata) => { if (iata) setOrigin(iata); }}
            placeholder="出発地（例: 東京、HND）"
            required
          />
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-blue-200 mb-0.5 block">出発日（から）</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full rounded-lg px-3 py-2.5 text-gray-800 text-sm focus:outline-none"
                required
              />
            </div>
            <div>
              <label className="text-xs text-blue-200 mb-0.5 block">出発日（まで）</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full rounded-lg px-3 py-2.5 text-gray-800 text-sm focus:outline-none"
                required
              />
            </div>
          </div>
          <select
            value={maxPrice}
            onChange={(e) => setMaxPrice(Number(e.target.value))}
            className="w-full rounded-lg px-3 py-2.5 text-gray-800 text-sm focus:outline-none"
          >
            {BUDGET_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <button
            type="submit"
            className="w-full flex items-center justify-center gap-2 bg-yellow-400 text-gray-900 font-semibold rounded-lg py-3 text-sm"
          >
            <Search size={16} /> どこでも検索
          </button>
        </form>
      </div>

      {/* フィルター */}
      {searching && (
        <div className="bg-white border-b border-gray-200 px-4 py-2 flex gap-2">
          {[
            { value: "all",           label: "すべて" },
            { value: "domestic",      label: "国内のみ" },
            { value: "international", label: "海外のみ" },
          ].map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value as typeof filter)}
              className={`px-3 py-1.5 rounded-full border text-sm ${
                filter === f.value
                  ? "bg-blue-600 text-white border-blue-600"
                  : "border-gray-300 text-gray-600"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      )}

      {/* 結果一覧 */}
      <div className="px-4 py-3 space-y-2">
        {isLoading && (
          <>
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-20 bg-white rounded-xl animate-pulse" />
            ))}
          </>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
            検索に失敗しました。しばらくしてから再度お試しください。
          </div>
        )}

        {filtered.map((dest: InspireDestination) => (
          <div
            key={dest.destination_iata}
            className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-between"
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold text-gray-800">{dest.destination_iata}</span>
                {dest.destination_name && (
                  <span className="text-sm text-gray-500">{dest.destination_name}</span>
                )}
              </div>
              {dest.cheapest_date && (
                <p className="text-xs text-gray-400 mt-0.5">
                  最安日: {new Date(dest.cheapest_date).toLocaleDateString("ja-JP", { month: "numeric", day: "numeric" })}
                </p>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span className="text-blue-600 font-bold">{formatPrice(dest.min_price_jpy)}</span>
              <button
                onClick={() =>
                  router.push(
                    `/flights/search?origin=${origin}&destination=${dest.destination_iata}&departure_date=${dateFrom}`
                  )
                }
                className="flex items-center gap-1 bg-blue-600 text-white rounded-lg px-3 py-2 text-sm font-medium"
              >
                検索 <ArrowRight size={13} />
              </button>
            </div>
          </div>
        ))}

        {searching && !isLoading && filtered.length === 0 && !error && (
          <p className="text-center text-gray-500 py-8">該当する行先が見つかりませんでした</p>
        )}
      </div>
    </div>
  );
}
