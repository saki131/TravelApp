"use client";
import { useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { flightApi } from "@/lib/api/flights";
import { formatPrice } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";
import type { PriceCalendarItem } from "@/types/flight";

function getPriceColor(price: number | null, prices: (number | null)[]): string {
  if (price === null) return "bg-gray-100 text-gray-400";
  const valid = prices.filter((p): p is number => p !== null);
  if (!valid.length) return "bg-gray-100";
  const min = Math.min(...valid);
  const max = Math.max(...valid);
  const range = max - min || 1;
  const ratio = (price - min) / range;

  if (ratio < 0.33) return "bg-green-100 text-green-800 font-semibold";
  if (ratio < 0.66) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-700";
}

export default function PriceCalendarPageContent() {
  const router = useRouter();
  const sp = useSearchParams();
  const origin      = sp.get("origin") ?? "HND";
  const destination = sp.get("destination") ?? "";

  const now = new Date();
  const [year, setYear]   = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const { data, isLoading } = useQuery({
    queryKey: ["price-calendar", origin, destination, year, month],
    queryFn: () => flightApi.priceCalendar(origin, destination, year, month),
    enabled: !!destination,
  });

  const prices = data?.prices ?? [];
  const priceValues = prices.map((p) => p.price_jpy);
  const cheapest    = prices.reduce((acc, p) => (p.price_jpy && (!acc || p.price_jpy < (acc.price_jpy ?? Infinity)) ? p : acc), null as PriceCalendarItem | null);

  const prevMonth = () => { if (month === 1) { setYear(y => y - 1); setMonth(12); } else setMonth(m => m - 1); };
  const nextMonth = () => { if (month === 12) { setYear(y => y + 1); setMonth(1); } else setMonth(m => m + 1); };

  // カレンダー用グリッド生成
  const firstDay = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();
  const cells: (PriceCalendarItem | null)[] = [
    ...Array(firstDay).fill(null),
    ...prices,
    ...Array((7 - (firstDay + daysInMonth) % 7) % 7).fill(null),
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-blue-600 text-white px-4 pt-10 pb-4">
        <button onClick={() => router.back()} className="flex items-center gap-1 text-blue-200 text-sm mb-2">
          <ArrowLeft size={16} /> 戻る
        </button>
        <h1 className="font-bold">価格カレンダー</h1>
        <p className="text-blue-200 text-sm">{origin} → {destination}</p>
      </div>

      <div className="px-4 py-4">
        {/* 月ナビゲーション */}
        <div className="flex items-center justify-between mb-3">
          <button onClick={prevMonth} className="p-2 rounded-full bg-white border border-gray-200">◀</button>
          <span className="font-semibold text-gray-800">{year}年{month}月</span>
          <button onClick={nextMonth} className="p-2 rounded-full bg-white border border-gray-200">▶</button>
        </div>

        {cheapest && cheapest.price_jpy && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-3 mb-3 text-sm text-green-800">
            今月最安: <span className="font-bold">{new Date(cheapest.date).toLocaleDateString("ja-JP", { day: "numeric" })}日</span>
            （{formatPrice(cheapest.price_jpy)}）
          </div>
        )}

        {/* 曜日ヘッダー */}
        <div className="grid grid-cols-7 mb-1">
          {["日","月","火","水","木","金","土"].map((d) => (
            <div key={d} className="text-center text-xs text-gray-500 py-1">{d}</div>
          ))}
        </div>

        {/* 日付グリッド */}
        {isLoading ? (
          <div className="grid grid-cols-7 gap-1">
            {[...Array(35)].map((_, i) => (
              <div key={i} className="aspect-square rounded bg-gray-200 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-7 gap-1">
            {cells.map((cell, i) => {
              if (!cell) return <div key={i} />;
              const dayNum = new Date(cell.date).getDate();
              const colorClass = getPriceColor(cell.price_jpy, priceValues);
              return (
                <button
                  key={i}
                  onClick={() => cell.price_jpy && router.push(
                    `/flights/search?origin=${origin}&destination=${destination}&departure_date=${cell.date}`
                  )}
                  className={`aspect-square rounded-lg flex flex-col items-center justify-center text-xs ${colorClass}`}
                >
                  <span className="font-medium">{dayNum}</span>
                  {cell.price_jpy && (
                    <span className="text-xs leading-none" style={{ fontSize: "0.6rem" }}>
                      ¥{(cell.price_jpy / 1000).toFixed(0)}k
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* 凡例 */}
        <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-100 inline-block"/>安い</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-yellow-100 inline-block"/>普通</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-100 inline-block"/>高い</span>
        </div>
      </div>
    </div>
  );
}
