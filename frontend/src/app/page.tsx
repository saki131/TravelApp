import Link from "next/link";
import TodaySales from "@/components/sale/TodaySales";
import FlightSearchForm from "@/components/search/FlightSearchForm";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* ヘッダー */}
      <header className="bg-blue-600 text-white px-4 pt-12 pb-6">
        <h1 className="text-xl font-bold tracking-tight mb-4">✈ TravelApp</h1>
        <FlightSearchForm />
      </header>

      {/* 今週のセール */}
      <section className="px-4 py-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-gray-800">今週のセール</h2>
          <Link href="/calendar" className="text-sm text-blue-600 font-medium">
            すべて見る →
          </Link>
        </div>
        <TodaySales />
      </section>
    </div>
  );
}
