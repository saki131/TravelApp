"use client";
import { useQuery } from "@tanstack/react-query";
import { saleApi } from "@/lib/api/sales";
import SaleCard from "./SaleCard";

export default function TodaySales() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["sales", "today"],
    queryFn: saleApi.today,
  });

  if (isLoading) {
    return (
      <div className="flex gap-3 overflow-x-auto pb-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="min-w-[140px] h-28 rounded-xl bg-gray-200 animate-pulse" />
        ))}
      </div>
    );
  }

  if (error || !data?.items.length) {
    return <p className="text-sm text-gray-500">現在セール情報はありません</p>;
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4">
      {data.items.slice(0, 8).map((sale) => (
        <SaleCard key={sale.id} sale={sale} />
      ))}
    </div>
  );
}
