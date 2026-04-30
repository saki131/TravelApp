import Link from "next/link";
import type { SaleEvent } from "@/types/sale";
import { formatPrice } from "@/lib/utils";
import { Plane, Hotel, Package, ExternalLink, BadgeCheck, ShoppingCart, MapPin } from "lucide-react";

const CATEGORY_META = {
  flight:  { icon: Plane,   bg: "bg-blue-50",   border: "border-blue-200",  text: "text-blue-700",   badge: "bg-blue-100 text-blue-700" },
  hotel:   { icon: Hotel,   bg: "bg-green-50",  border: "border-green-200", text: "text-green-700",  badge: "bg-green-100 text-green-700" },
  package: { icon: Package, bg: "bg-orange-50", border: "border-orange-200", text: "text-orange-700", badge: "bg-orange-100 text-orange-700" },
};

const SOURCE_LABEL: Record<string, string> = {
  peach:         "Peach",
  jetstar:       "Jetstar",
  spring_japan:  "Spring Japan",
  jal:           "JAL",
  ana:           "ANA",
  rakuten_travel:"楽天トラベル",
  jtb:           "JTB",
};

const SOURCE_COLOR: Record<string, string> = {
  peach:         "bg-pink-100 text-pink-700",
  jetstar:       "bg-orange-100 text-orange-700",
  spring_japan:  "bg-yellow-100 text-yellow-800",
  jal:           "bg-red-100 text-red-700",
  ana:           "bg-blue-100 text-blue-700",
  rakuten_travel:"bg-rose-100 text-rose-700",
  jtb:           "bg-purple-100 text-purple-700",
};

function fmt(s: string): string {
  return new Date(s).toLocaleDateString("ja-JP", { month: "numeric", day: "numeric" });
}

/** 購入期間の表示文字列とラベルを返す */
function bookingInfo(start?: string | null, end?: string | null): { label: string; text: string } | null {
  if (start && end) return { label: "購入期間", text: `${fmt(start)}〜${fmt(end)}` };
  if (end)          return { label: "予約締切", text: `${fmt(end)}まで` };
  if (start)        return { label: "購入開始", text: `${fmt(start)}〜` };
  return null;
}

/** 搭乗期間の表示文字列とラベルを返す */
function travelInfo(start?: string | null, end?: string | null): { label: string; text: string } | null {
  if (start && end) return { label: "搭乗期間", text: `${fmt(start)}〜${fmt(end)}` };
  if (end)          return { label: "搭乗締切", text: `${fmt(end)}まで` };
  if (start)        return { label: "搭乗開始", text: `${fmt(start)}〜` };
  return null;
}

export default function SaleCard({ sale }: { sale: SaleEvent }) {
  const meta = CATEGORY_META[sale.category] ?? CATEGORY_META.flight;
  const Icon = meta.icon;
  const airlineName = SOURCE_LABEL[sale.source] ?? sale.source;
  const airlineColor = SOURCE_COLOR[sale.source] ?? "bg-gray-100 text-gray-600";
  const booking = bookingInfo(sale.sale_start, sale.sale_end);
  const travel  = travelInfo(sale.travel_start, sale.travel_end);

  // 予約締切が過去かどうか
  const isExpired = sale.sale_end ? new Date(sale.sale_end) < new Date() : false;

  return (
    <div className={`rounded-xl border flex flex-col ${meta.bg} ${meta.border} ${isExpired ? "opacity-60" : ""}`}>
      {isExpired && (
        <div className="text-center text-[10px] font-semibold text-white bg-gray-400 rounded-t-xl px-2 py-0.5">
          受付終了
        </div>
      )}
      {/* カード本体 → 詳細ページへ */}
      <Link
        href={`/sales/${sale.id}`}
        className="p-3 flex flex-col gap-2 flex-1 active:opacity-70 transition-opacity"
      >
        {/* 航空会社 + カテゴリ */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded-md ${airlineColor}`}>
            {airlineName}
          </span>
          <span className={`flex items-center gap-0.5 text-[11px] font-semibold px-1.5 py-0.5 rounded-md ${meta.badge}`}>
            <Icon size={11} />
            {sale.category === "flight" ? "飛行機" : sale.category === "hotel" ? "ホテル" : "旅行パック"}
          </span>
          {sale.is_verified && <BadgeCheck size={13} className="text-green-500 ml-auto shrink-0" />}
        </div>

        {/* タイトル */}
        <p className="text-sm font-semibold text-gray-800 leading-tight line-clamp-2">{sale.title}</p>

        {/* 購入期間・搭乗期間 */}
        <div className="space-y-0.5">
          {booking ? (
            <div className="flex items-center gap-1 text-[11px] text-gray-600">
              <ShoppingCart size={11} className="shrink-0 text-gray-400" />
              <span className="font-medium text-gray-500 shrink-0">{booking.label}</span>
              <span className={isExpired ? "line-through text-gray-400" : ""}>{booking.text}</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 text-[11px] text-gray-400">
              <ShoppingCart size={11} className="shrink-0" />
              <span>購入期間: 未確認</span>
            </div>
          )}
          {travel ? (
            <div className="flex items-center gap-1 text-[11px] text-gray-600">
              <MapPin size={11} className="shrink-0 text-gray-400" />
              <span className="font-medium text-gray-500 shrink-0">{travel.label}</span>
              <span>{travel.text}</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 text-[11px] text-gray-400">
              <MapPin size={11} className="shrink-0" />
              <span>搭乗期間: 未確認</span>
            </div>
          )}
        </div>

        {/* 価格・割引 */}
        <div className="flex items-center gap-2 mt-auto">
          {sale.discount_rate && (
            <span className="bg-red-500 text-white text-[11px] px-1.5 py-0.5 rounded-full font-bold">
              {sale.discount_rate}% OFF
            </span>
          )}
          {sale.min_price_jpy && (
            <span className="text-xs text-gray-600">{formatPrice(sale.min_price_jpy)}〜</span>
          )}
        </div>
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
