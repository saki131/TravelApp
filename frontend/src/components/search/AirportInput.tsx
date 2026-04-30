"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { flightApi } from "@/lib/api/flights";

type Airport = {
  iata_code: string;
  name_ja: string;
  city_ja: string;
  country_code: string;
};

type Props = {
  value: string;           // IATA コード（HND 等）
  onChange: (iata: string) => void;
  placeholder?: string;
  required?: boolean;
};

export default function AirportInput({ value, onChange, placeholder, required }: Props) {
  const [query, setQuery] = useState(value); // 表示テキスト
  const [suggestions, setSuggestions] = useState<Airport[]>([]);
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // value が外部から変わった場合に表示テキストも更新（初期値など）
  useEffect(() => {
    if (value && !query) setQuery(value);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 外クリックで閉じる
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const search = useCallback(async (q: string) => {
    if (q.length < 1) { setSuggestions([]); setOpen(false); return; }
    try {
      const results = await flightApi.suggestAirports(q);
      setSuggestions(results as unknown as Airport[]);
      setOpen(results.length > 0);
      setActiveIdx(-1);
    } catch {
      setSuggestions([]); setOpen(false);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    onChange(""); // IATA 未確定状態にリセット
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => search(val), 250);
  };

  const select = (airport: Airport) => {
    setQuery(`${airport.city_ja}（${airport.iata_code}）`);
    onChange(airport.iata_code);
    setSuggestions([]);
    setOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && activeIdx >= 0) {
      e.preventDefault();
      select(suggestions[activeIdx]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={containerRef} className="relative">
      <input
        value={query}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={() => { if (suggestions.length > 0) setOpen(true); }}
        placeholder={placeholder}
        required={required}
        autoComplete="off"
        className="w-full rounded-lg px-3 py-2.5 text-gray-800 text-sm focus:outline-none"
      />
      {open && suggestions.length > 0 && (
        <ul className="absolute z-50 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-56 overflow-y-auto text-sm">
          {suggestions.map((a, i) => (
            <li
              key={a.iata_code}
              onMouseDown={() => select(a)}
              className={`px-4 py-2.5 cursor-pointer flex justify-between items-center gap-2 ${
                i === activeIdx ? "bg-blue-50" : "hover:bg-gray-50"
              }`}
            >
              <span className="text-gray-800">
                {a.city_ja}
                {a.name_ja && a.name_ja !== a.city_ja && (
                  <span className="text-gray-500 text-xs ml-1">({a.name_ja})</span>
                )}
              </span>
              <span className="font-mono font-bold text-blue-600 text-xs shrink-0">{a.iata_code}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
