import { Suspense } from "react";
import PriceCalendarPageContent from "@/components/flight/PriceCalendarPageContent";

export const metadata = { title: "価格カレンダー | TravelApp" };

export default function Page() {
  return (
    <Suspense fallback={<div className="flex justify-center pt-20 text-gray-400">読み込み中...</div>}>
      <PriceCalendarPageContent />
    </Suspense>
  );
}
