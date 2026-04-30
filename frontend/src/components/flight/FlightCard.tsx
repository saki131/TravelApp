import type { FlightItinerary } from "@/types/flight";
import { formatPrice, formatDuration, formatDateTime } from "@/lib/utils";
import { ExternalLink, Plane } from "lucide-react";

export default function FlightCard({ flight }: { flight: FlightItinerary }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-2">
      {/* 航空会社 + 価格 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Plane size={16} className="text-blue-500" />
          <span className="font-semibold text-gray-800 text-sm">
            {flight.airline_name ?? flight.airline_code}
          </span>
          <span className="text-xs text-gray-400">{flight.flight_numbers.join(" / ")}</span>
        </div>
        <span className="text-blue-600 font-bold text-base">{formatPrice(flight.price_jpy)}</span>
      </div>

      {/* 時刻 */}
      <div className="flex items-center gap-2 text-sm">
        <div className="text-center">
          <p className="font-semibold text-gray-900">
            {new Date(flight.departure_time).toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" })}
          </p>
          <p className="text-xs text-gray-500">{flight.departure_iata}</p>
        </div>
        <div className="flex-1 flex flex-col items-center text-xs text-gray-400 gap-0.5">
          <span>{formatDuration(flight.duration_minutes)}</span>
          <div className="w-full flex items-center gap-1">
            <div className="h-px flex-1 bg-gray-300" />
            <Plane size={10} className="text-gray-400" />
            <div className="h-px flex-1 bg-gray-300" />
          </div>
          <span>{flight.stops === 0 ? "直行" : `乗継${flight.stops}回`}</span>
        </div>
        <div className="text-center">
          <p className="font-semibold text-gray-900">
            {new Date(flight.arrival_time).toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" })}
          </p>
          <p className="text-xs text-gray-500">{flight.arrival_iata}</p>
        </div>
      </div>

      {/* 予約ボタン */}
      {flight.booking_url ? (
        <a
          href={flight.booking_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-1.5 w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-semibold"
        >
          予約サイトへ <ExternalLink size={13} />
        </a>
      ) : (
        <p className="text-xs text-center text-gray-400">予約リンク取得中</p>
      )}
    </div>
  );
}
