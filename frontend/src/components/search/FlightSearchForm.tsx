"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSearchStore } from "@/lib/store/searchStore";
import { Search } from "lucide-react";
import AirportInput from "./AirportInput";

export default function FlightSearchForm() {
  const router = useRouter();
  const { origin, destination, departureDate, returnDate, setOrigin, setDestination, setDepartureDate, setReturnDate } =
    useSearchStore();
  const [tripType, setTripType] = useState<"one-way" | "round">("one-way");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!origin || !departureDate) return;

    if (destination === "ANYWHERE" || !destination) {
      router.push(`/inspire?origin=${origin}&date_from=${departureDate}&date_to=${departureDate}`);
    } else {
      const params = new URLSearchParams({
        origin,
        destination,
        departure_date: departureDate,
        ...(tripType === "round" && returnDate ? { return_date: returnDate } : {}),
      });
      router.push(`/flights/search?${params}`);
    }
  };

  return (
    <form onSubmit={handleSearch} className="space-y-2">
      {/* 片道 / 往復 */}
      <div className="flex gap-2 text-sm">
        {(["one-way", "round"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTripType(t)}
            className={`px-3 py-1 rounded-full border transition-colors ${
              tripType === t
                ? "bg-white text-blue-600 border-white font-semibold"
                : "text-white border-blue-400"
            }`}
          >
            {t === "one-way" ? "片道" : "往復"}
          </button>
        ))}
      </div>

      {/* 出発地 / 目的地 */}
      <div className="grid grid-cols-2 gap-2">
        <AirportInput
          value={origin}
          onChange={setOrigin}
          placeholder="出発地（例: 東京）"
          required
        />
        <AirportInput
          value={destination}
          onChange={setDestination}
          placeholder="行先（どこでも = 空欄）"
        />
      </div>

      {/* 日付 */}
      <div className="grid grid-cols-2 gap-2">
        <input
          type="date"
          value={departureDate}
          onChange={(e) => setDepartureDate(e.target.value)}
          className="w-full rounded-lg px-3 py-2.5 text-gray-800 text-sm focus:outline-none"
          required
        />
        {tripType === "round" && (
          <input
            type="date"
            value={returnDate}
            onChange={(e) => setReturnDate(e.target.value)}
            className="w-full rounded-lg px-3 py-2.5 text-gray-800 text-sm focus:outline-none"
          />
        )}
      </div>

      <button
        type="submit"
        className="w-full flex items-center justify-center gap-2 bg-yellow-400 text-gray-900 font-semibold rounded-lg py-3 text-sm active:bg-yellow-500 transition-colors"
      >
        <Search size={16} />
        フライトを検索
      </button>
    </form>
  );
}
