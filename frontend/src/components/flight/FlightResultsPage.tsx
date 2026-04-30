"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { flightApi } from "@/lib/api/flights";
import FlightCard from "./FlightCard";
import { ArrowLeft, SlidersHorizontal } from "lucide-react";
import { useState } from "react";

export default function FlightResultsPage() {
  const router = useRouter();
  const sp = useSearchParams();
  const origin       = sp.get("origin") ?? "";
  const destination  = sp.get("destination") ?? "";
  const departureDate = sp.get("departure_date") ?? "";
  const returnDate   = sp.get("return_date") ?? undefined;

  const [nonstopOnly, setNonstopOnly] = useState(false);
  const [sortKey, setSortKey] = useState<"price" | "duration">("price");

  const { data, isLoading, error } = useQuery({
    queryKey: ["flights", origin, destination, departureDate, returnDate, nonstopOnly],
    queryFn: () =>
      flightApi.search({
        origin,
        destination,
        departure_date: departureDate,
        return_date: returnDate,
        nonstop_only: nonstopOnly,
      }),
    enabled: !!origin && !!destination && !!departureDate,
  });

  const sorted = [...(data?.results ?? [])].sort((a, b) =>
    sortKey === "price"
      ? a.price_jpy - b.price_jpy
      : a.duration_minutes - b.duration_minutes
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <div className="bg-blue-600 text-white px-4 pt-10 pb-4">
        <button onClick={() => router.back()} className="flex items-center gap-1 text-blue-200 text-sm mb-2">
          <ArrowLeft size={16} /> 戻る
        </button>
        <h1 className="text-base font-bold">
          {origin} → {destination}
        </h1>
        <p className="text-blue-200 text-sm">{departureDate}{returnDate ? ` / 帰り: ${returnDate}` : ""}</p>
      </div>

      {/* フィルターバー */}
      <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between gap-3">
        <div className="flex gap-2 text-sm">
          <button
            onClick={() => setSortKey("price")}
            className={`px-3 py-1.5 rounded-full border text-sm ${sortKey === "price" ? "bg-blue-600 text-white border-blue-600" : "border-gray-300 text-gray-600"}`}
          >
            価格順
          </button>
          <button
            onClick={() => setSortKey("duration")}
            className={`px-3 py-1.5 rounded-full border text-sm ${sortKey === "duration" ? "bg-blue-600 text-white border-blue-600" : "border-gray-300 text-gray-600"}`}
          >
            所要時間順
          </button>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input type="checkbox" checked={nonstopOnly} onChange={(e) => setNonstopOnly(e.target.checked)} />
          直行のみ
        </label>
      </div>

      {/* 結果一覧 */}
      <div className="px-4 py-3 space-y-3">
        {isLoading && (
          <>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-28 bg-white rounded-xl animate-pulse" />
            ))}
          </>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
            フライト情報の取得に失敗しました。外部 API の制限に達している可能性があります。
          </div>
        )}

        {!isLoading && sorted.length === 0 && !error && (
          <div className="text-center py-12 text-gray-500">
            <p>該当するフライトが見つかりませんでした</p>
            <p className="text-xs mt-1">条件を変更して再検索してください</p>
          </div>
        )}

        {sorted.map((flight) => (
          <FlightCard key={flight.id} flight={flight} />
        ))}

        {/* 外部リンク */}
        {!isLoading && (
          <div className="bg-white rounded-xl border border-gray-200 p-4 text-sm">
            <p className="text-gray-500 mb-2 font-medium">他のサイトでも確認する</p>
            <div className="flex flex-wrap gap-2">
              {[
                { label: "Skyscanner", url: `https://www.skyscanner.jp/transport/flights/${origin}/${destination}/${departureDate.replace(/-/g, "")}/` },
                { label: "Google Flights", url: `https://www.google.com/travel/flights?q=${origin}+to+${destination}` },
                { label: "Trip.com", url: `https://www.trip.com/flights/` },
              ].map(({ label, url }) => (
                <a
                  key={label}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 rounded-full border border-gray-300 text-gray-600 text-xs"
                >
                  {label} →
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
