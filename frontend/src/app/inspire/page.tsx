import { Suspense } from "react";
import InspirePage from "@/components/flight/InspirePage";

export const metadata = { title: "どこでも検索 | TravelApp" };

export default function Page() {
  return (
    <Suspense fallback={<div className="flex justify-center pt-20 text-gray-400">読み込み中...</div>}>
      <InspirePage />
    </Suspense>
  );
}
