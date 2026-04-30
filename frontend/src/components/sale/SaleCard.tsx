import Link from "next/link";
import type { SaleEvent } from "@/types/sale";
import { formatPrice } from "@/lib/utils";
import { Plane, Hotel, Package, ExternalLink, BadgeCheck } from "lucide-react";

const CATEGORY_META = {
  flight:  { icon: Plane,   bg: "bg-blue-50",   border: "border-blue-200",  text: "text-blue-700" },
  hotel:   { icon: Hotel,   bg: "bg-green-50",  border: "border-green-200", text: "text-green-700" },
  package: { icon: Package, bg: "bg-orange-50", border: "border-orange-200", text: "text-orange-700" },
};

export default function SaleCard({ sale }: { sale: SaleEvent }) {
  const meta = CATEGORY_META[sale.category] ?? CATEGORY_META.flight;
  const Icon = meta.icon;

  return (
    <div className={`min-w-[152px] rounded-xl border flex flex-col ${meta.bg} ${meta.border}`}>
      {/* カード本体 → 詳細ページへ */}
      <Link
        href={`/sales/${sale.id}`}
        className="p-3 flex flex-col gap-1.5 flex-1 active:opacity-70 transition-opacity"
      >
        <div className={`flex items-center gap-1 text-xs font-semibold ${meta.text}`}>
          <Icon size={13} />
          {sale.category === "flight" ? "飛行機" : sale.category === "hotel" ? "ホテル" : "旅行パック"}
          {sale.is_verified && (
            <BadgeCheck size={13} className="ml-auto text-green-500 shrink-0" />
          )}
        </div>
        <p className="text-sm font-semibold text-gray-800 leading-tight line-clamp-2">{sale.title}</p>
        {sale.min_price_jpy && (
          <p className="text-xs text-gray-600 mt-auto">{formatPrice(sale.min_price_jpy)}〜</p>
        )}
        {sale.discount_rate && (
          <span className="self-start bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full font-bold">
            {sale.discount_rate}% OFF
          </span>
        )}
        {sale.sale_end && (
          <p className="text-xs text-gray-500">
            〜{new Date(sale.sale_end).toLocaleDateString("ja-JP", { month: "numeric", day: "numeric" })}迄
          </p>
        )}
      </Link>

      {/* 公式サイトボタン */}
      {sale.booking_url && (
        <a
          href={sale.booking_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="flex items-center justify-center gap-1 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-b-xl transition-colors"
        >
          公式サイトへ
          <ExternalLink size={11} />
        </a>
      )}
    </div>
  );
}
