"use client";
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { saleApi } from "@/lib/api/sales";
import SaleCard from "./SaleCard";
import { ChevronLeft, ChevronRight, CalendarDays, List } from "lucide-react";
import type { SaleEvent } from "@/types/sale";

const CATEGORIES = [
  { value: "", label: "すべて" },
  { value: "flight", label: "✈ 飛行機" },
  { value: "hotel", label: "🏨 ホテル" },
  { value: "package", label: "🎒 旅行パック" },
];

const SOURCE_COLOR: Record<string, string> = {
  peach:        "bg-pink-400",
  jetstar:      "bg-orange-400",
  spring_japan: "bg-yellow-400",
  jal:          "bg-red-500",
  ana:          "bg-blue-500",
  rakuten_travel:"bg-rose-400",
  jtb:          "bg-purple-500",
};

function getColor(source: string) {
  return SOURCE_COLOR[source] ?? "bg-gray-400";
}

function isoToDate(s?: string): Date | null {
  if (!s) return null;
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d;
}

export default function SaleCalendarPage() {
  const [category, setCategory] = useState("");
  const [view, setView] = useState<"calendar" | "list">("calendar");
  const today = new Date();
  const [calMonth, setCalMonth] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [selectedDate, setSelectedDate] = useState<string | null>(today.toISOString().slice(0, 10));

  const { data, isLoading } = useQuery({
    queryKey: ["sales", "list", category],
    queryFn: () => saleApi.list({ category: category || undefined, limit: 100 }),
  });

  // カレンダー用: 月の日付グリッド生成
  const calDays = useMemo(() => {
    const year = calMonth.getFullYear();
    const month = calMonth.getMonth();
    const firstDay = new Date(year, month, 1).getDay(); // 0=日
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const cells: (number | null)[] = Array(firstDay).fill(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);
    while (cells.length % 7 !== 0) cells.push(null);
    return cells;
  }, [calMonth]);

  // 各日に有効なセールを紐付け
  const salesByDate = useMemo(() => {
    const map: Record<string, SaleEvent[]> = {};
    const items = data?.items ?? [];
    const year = calMonth.getFullYear();
    const month = calMonth.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      const dayMs = new Date(dateStr).getTime();
      map[dateStr] = items.filter((s) => {
        const start = isoToDate(s.sale_start)?.getTime() ?? -Infinity;
        const end = isoToDate(s.sale_end)?.getTime() ?? Infinity;
        return dayMs >= start && dayMs <= end;
      });
    }
    return map;
  }, [data, calMonth]);

  // 選択日のセール一覧
  const selectedSales = useMemo(() => {
    if (!selectedDate) return data?.items ?? [];
    return salesByDate[selectedDate] ?? [];
  }, [selectedDate, salesByDate, data]);

  const prevMonth = () => setCalMonth(new Date(calMonth.getFullYear(), calMonth.getMonth() - 1, 1));
  const nextMonth = () => setCalMonth(new Date(calMonth.getFullYear(), calMonth.getMonth() + 1, 1));

  const monthLabel = calMonth.toLocaleDateString("ja-JP", { year: "numeric", month: "long" });

  return (
    <div className="pt-4 pb-24">
      {/* ヘッダー */}
      <div className="px-4 flex items-center justify-between mb-3">
        <h1 className="text-lg font-bold text-gray-800">セール・クーポンカレンダー</h1>
        <div className="flex gap-1">
          <button
            onClick={() => setView("calendar")}
            className={`p-1.5 rounded-lg ${view === "calendar" ? "bg-blue-600 text-white" : "text-gray-400"}`}
          >
            <CalendarDays size={18} />
          </button>
          <button
            onClick={() => setView("list")}
            className={`p-1.5 rounded-lg ${view === "list" ? "bg-blue-600 text-white" : "text-gray-400"}`}
          >
            <List size={18} />
          </button>
        </div>
      </div>

      {/* カテゴリフィルター */}
      <div className="px-4 flex gap-2 overflow-x-auto pb-2 mb-3">
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

      {/* ===== カレンダービュー ===== */}
      {view === "calendar" && (
        <>
          {/* 月ナビ */}
          <div className="px-4 flex items-center justify-between mb-2">
            <button onClick={prevMonth} className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100">
              <ChevronLeft size={20} />
            </button>
            <span className="text-sm font-semibold text-gray-700">{monthLabel}</span>
            <button onClick={nextMonth} className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100">
              <ChevronRight size={20} />
            </button>
          </div>

          {/* 曜日ヘッダー */}
          <div className="px-2 grid grid-cols-7 mb-1">
            {["日","月","火","水","木","金","土"].map((d, i) => (
              <div key={d} className={`text-center text-xs font-medium py-1 ${i === 0 ? "text-red-500" : i === 6 ? "text-blue-500" : "text-gray-500"}`}>
                {d}
              </div>
            ))}
          </div>

          {/* 日付グリッド */}
          <div className="px-2 grid grid-cols-7 gap-px">
            {calDays.map((day, idx) => {
              if (day === null) return <div key={`empty-${idx}`} />;
              const dateStr = `${calMonth.getFullYear()}-${String(calMonth.getMonth() + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
              const sales = salesByDate[dateStr] ?? [];
              const isToday = dateStr === today.toISOString().slice(0, 10);
              const isSelected = dateStr === selectedDate;
              const dow = (new Date(dateStr).getDay());
              return (
                <button
                  key={dateStr}
                  onClick={() => setSelectedDate(isSelected ? null : dateStr)}
                  className={`relative flex flex-col items-center pt-1 pb-0.5 rounded-lg min-h-[52px] transition-colors ${
                    isSelected ? "bg-blue-100 ring-2 ring-blue-400" : "hover:bg-gray-50"
                  }`}
                >
                  <span className={`text-xs font-semibold w-6 h-6 flex items-center justify-center rounded-full ${
                    isToday ? "bg-blue-600 text-white" :
                    dow === 0 ? "text-red-500" : dow === 6 ? "text-blue-500" : "text-gray-700"
                  }`}>{day}</span>
                  <div className="flex flex-col gap-0.5 w-full px-0.5 mt-0.5">
                    {sales.slice(0, 3).map((s) => (
                      <div key={s.id} className={`h-1 rounded-full ${getColor(s.source)}`} />
                    ))}
                    {sales.length > 3 && (
                      <span className="text-[9px] text-gray-400 leading-none text-center">+{sales.length - 3}</span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          {/* 凡例 */}
          <div className="px-4 mt-3 flex flex-wrap gap-2">
            {Object.entries(SOURCE_COLOR).map(([src, cls]) => (
              <div key={src} className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${cls}`} />
                <span className="text-xs text-gray-500">{src.replace("_", " ")}</span>
              </div>
            ))}
          </div>

          {/* 選択日のセール一覧 */}
          <div className="px-4 mt-4">
            <p className="text-sm font-semibold text-gray-700 mb-2">
              {selectedDate
                ? `${new Date(selectedDate).toLocaleDateString("ja-JP", { month: "long", day: "numeric" })} のセール（${selectedSales.length}件）`
                : `全セール（${data?.items.length ?? 0}件）`}
            </p>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => <div key={i} className="h-20 rounded-xl bg-gray-200 animate-pulse" />)}
              </div>
            ) : selectedSales.length === 0 ? (
              <p className="text-center text-gray-400 py-6 text-sm">この日に開催中のセールはありません</p>
            ) : (
              <div className="space-y-2">
                {selectedSales.map((sale) => <SaleCard key={sale.id} sale={sale} />)}
              </div>
            )}
          </div>
        </>
      )}

      {/* ===== リストビュー ===== */}
      {view === "list" && (
        <div className="px-4">
          {isLoading ? (
            <div className="grid grid-cols-2 gap-3">
              {[...Array(6)].map((_, i) => <div key={i} className="h-32 rounded-xl bg-gray-200 animate-pulse" />)}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {data?.items.map((sale) => <SaleCard key={sale.id} sale={sale} />)}
            </div>
          )}
          {!isLoading && !data?.items.length && (
            <p className="text-center text-gray-500 py-8">セール情報がありません</p>
          )}
        </div>
      )}
    </div>
  );
}
