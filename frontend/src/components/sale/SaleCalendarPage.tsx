"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { saleApi } from "@/lib/api/sales";
import SaleCard from "./SaleCard";

const CATEGORIES = [
  { value: "", label: "すべて" },
  { value: "flight", label: "✈ 飛行機" },
  { value: "hotel", label: "🏨 ホテル" },
  { value: "package", label: "🎒 旅行パック" },
];

export default function SaleCalendarPage() {
  const [category, setCategory] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["sales", "list", category],
    queryFn: () => saleApi.list({ category: category || undefined, limit: 100 }),
  });

  return (
    <div className="px-4 pt-4">
      <h1 className="text-lg font-bold text-gray-800 mb-3">セール・クーポンカレンダー</h1>

      {/* カテゴリフィルター */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-4">
        {CATEGORIES.map((c) => (
          <button
            key={c.value}
            onClick={() => setCategory(c.value)}
            className={`whitespace-nowrap px-3 py-1.5 rounded-full text-sm border transition-colors ${
              category === c.value
                ? "bg-blue-600 text-white border-blue-600"
                : "border-gray-300 text-gray-600 bg-white"
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* グリッド表示 */}
      {isLoading ? (
        <div className="grid grid-cols-2 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-32 rounded-xl bg-gray-200 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {data?.items.map((sale) => (
            <SaleCard key={sale.id} sale={sale} />
          ))}
        </div>
      )}

      {!isLoading && !data?.items.length && (
        <p className="text-center text-gray-500 py-8">セール情報がありません</p>
      )}
    </div>
  );
}
