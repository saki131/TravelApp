import type { Metadata, Viewport } from "next";
import "./globals.css";
import { QueryProvider } from "@/components/providers/QueryProvider";
import BottomNav from "@/components/layout/BottomNav";

export const metadata: Metadata = {
  title: "TravelApp – フライト & セール",
  description: "最安フライト検索・セールカレンダー",
  manifest: "/manifest.json",
  appleWebApp: { capable: true, statusBarStyle: "default", title: "TravelApp" },
};

export const viewport: Viewport = {
  themeColor: "#2563eb",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <QueryProvider>
          <main>{children}</main>
          <BottomNav />
        </QueryProvider>
      </body>
    </html>
  );
}
