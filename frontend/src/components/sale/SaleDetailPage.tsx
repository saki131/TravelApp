"use client";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { saleApi } from "@/lib/api/sales";
import { formatPrice, formatDate } from "@/lib/utils";
import { ArrowLeft, Copy, ExternalLink, Plane } from "lucide-react";
import { useState } from "react";

export default function SaleDetailPage({ id }: { id: string }) {
  const router = useRouter();
  const { data: sale, isLoading } = useQuery({
    queryKey: ["sale", id],
    queryFn: () => saleApi.get(id),
  });
  const [copied, setCopied] = useState(false);

  const copyCoupon = () => {
    if (sale?.coupon_code) {
      navigator.clipboard.writeText(sale.coupon_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isLoading) {
    return (
      <div className="px-4 pt-4 space-y-3">
        <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
        <div className="h-40 bg-gray-200 rounded-xl animate-pulse" />
      </div>
    );
  }
  if (!sale) return <p className="p-4 text-gray-500">セール情報が見つかりません</p>;

  return (
    <div className="px-4 pt-4 space-y-4 max-w-lg mx-auto">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-blue-600 text-sm">
        <ArrowLeft size={16} /> 戻る
      </button>

      <div className="bg-white rounded-2xl border border-gray-200 p-4 space-y-3">
        <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
          {sale.category === "flight" ? "✈ 飛行機" : sale.category === "hotel" ? "🏨 ホテル" : "🎒 旅行パック"}
        </span>

        <h1 className="text-lg font-bold text-gray-900 leading-snug">{sale.title}</h1>

        {sale.description && <p className="text-sm text-gray-600">{sale.description}</p>}

        <div className="divide-y divide-gray-100 text-sm">
          {sale.sale_start && sale.sale_end && (
            <div className="py-2 flex justify-between">
              <span className="text-gray-500">予約期間</span>
              <span className="font-medium">
                {formatDate(sale.sale_start)} 〜 {formatDate(sale.sale_end)}
              </span>
            </div>
          )}
          {sale.travel_start && sale.travel_end && (
            <div className="py-2 flex justify-between">
              <span className="text-gray-500">搭乗期間</span>
              <span className="font-medium">
                {formatDate(sale.travel_start)} 〜 {formatDate(sale.travel_end)}
              </span>
            </div>
          )}
          {sale.discount_rate && (
            <div className="py-2 flex justify-between">
              <span className="text-gray-500">割引</span>
              <span className="font-bold text-red-600">{sale.discount_rate}% OFF</span>
            </div>
          )}
          {sale.min_price_jpy && (
            <div className="py-2 flex justify-between">
              <span className="text-gray-500">目安最低価格</span>
              <span className="font-semibold">{formatPrice(sale.min_price_jpy)}〜</span>
            </div>
          )}
        </div>

        {!sale.is_verified && (
          <p className="text-xs text-amber-600 bg-amber-50 p-3 rounded-lg">
            ※ この価格は目安です。実際の予約価格はフライト検索でご確認ください。
          </p>
        )}

        {sale.coupon_code && (
          <button
            onClick={copyCoupon}
            className="w-full flex items-center justify-between bg-gray-50 border border-dashed border-gray-300 rounded-xl px-4 py-3"
          >
            <div>
              <p className="text-xs text-gray-500">クーポンコード</p>
              <p className="font-mono font-semibold text-gray-800">{sale.coupon_code}</p>
            </div>
            <div className="flex items-center gap-1 text-blue-600 text-sm font-medium">
              <Copy size={14} />
              {copied ? "コピー済み" : "コピー"}
            </div>
          </button>
        )}

        <div className="flex flex-col gap-2">
          {sale.target_routes?.length ? (
            <a
              href={`/flights/search?origin=${sale.target_routes[0]?.origin ?? ""}&destination=${sale.target_routes[0]?.destination ?? ""}`}
              className="flex items-center justify-center gap-2 bg-blue-600 text-white rounded-xl py-3 text-sm font-semibold"
            >
              <Plane size={16} />
              この路線のフライトを検索
            </a>
          ) : null}
          {sale.booking_url && (
            <a
              href={sale.booking_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 border border-gray-300 text-gray-700 rounded-xl py-3 text-sm font-medium"
            >
              <ExternalLink size={15} />
              公式サイトで確認
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
