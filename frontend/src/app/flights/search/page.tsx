import { Suspense } from "react";
import FlightResultsPage from "@/components/flight/FlightResultsPage";

export const metadata = { title: "フライト検索結果 | TravelApp" };

export default function Page() {
  return (
    <Suspense fallback={<div className="flex justify-center pt-20 text-gray-400">読み込み中...</div>}>
      <FlightResultsPage />
    </Suspense>
  );
}
