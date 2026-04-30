"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, CalendarDays, Plane, Search, Heart } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/",          label: "トップ",       icon: Home },
  { href: "/calendar",  label: "カレンダー",   icon: CalendarDays },
  { href: "/flights/search", label: "フライト", icon: Plane },
  { href: "/inspire",   label: "どこでも",     icon: Search },
  { href: "/settings",  label: "お気に入り",   icon: Heart },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 flex h-16">
      {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || (href !== "/" && pathname.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-1 flex-col items-center justify-center gap-0.5 text-xs transition-colors",
              active ? "text-blue-600" : "text-gray-500"
            )}
          >
            <Icon size={22} strokeWidth={active ? 2.5 : 1.5} />
            <span>{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
