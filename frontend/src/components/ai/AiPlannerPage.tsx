"use client";

import { useState } from "react";
import { Sparkles, Send, MapPin, Calendar, Users } from "lucide-react";
import { apiFetch } from "@/lib/api/client";

interface PlanResult {
  plan: string;
}

export default function AiPlannerPage() {
  const [form, setForm] = useState({
    origin: "",
    destination: "",
    duration_days: 3,
    budget: "",
    preferences: "",
  });
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data: PlanResult = await apiFetch("/ai/plan", {
        method: "POST",
        body: JSON.stringify({
          origin: form.origin || undefined,
          destination: form.destination,
          duration_days: form.duration_days,
          budget: form.budget ? Number(form.budget) : undefined,
          preferences: form.preferences || undefined,
        }),
      });
      setResult(data.plan);
    } catch {
      setError("プランの生成に失敗しました。しばらくしてから再試行してください。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto pb-24 px-4 pt-6">
      <div className="flex items-center gap-2 mb-6">
        <Sparkles className="w-6 h-6 text-purple-600" />
        <h1 className="text-2xl font-bold text-gray-900">AI旅行プランナー</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <MapPin className="inline w-4 h-4 mr-1 text-gray-400" />
            出発地（任意）
          </label>
          <input
            type="text"
            value={form.origin}
            onChange={(e) => setForm({ ...form, origin: e.target.value })}
            placeholder="例: 東京、大阪"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <MapPin className="inline w-4 h-4 mr-1 text-gray-400" />
            目的地 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            required
            value={form.destination}
            onChange={(e) => setForm({ ...form, destination: e.target.value })}
            placeholder="例: パリ、バリ島、ソウル"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <Calendar className="inline w-4 h-4 mr-1 text-gray-400" />
            旅行日数
          </label>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={1}
              max={14}
              value={form.duration_days}
              onChange={(e) => setForm({ ...form, duration_days: Number(e.target.value) })}
              className="flex-1 accent-purple-600"
            />
            <span className="text-sm font-semibold text-purple-700 w-12 text-center">
              {form.duration_days}日
            </span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <Users className="inline w-4 h-4 mr-1 text-gray-400" />
            予算（円・任意）
          </label>
          <input
            type="number"
            value={form.budget}
            onChange={(e) => setForm({ ...form, budget: e.target.value })}
            placeholder="例: 150000"
            min={0}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            こだわり・リクエスト（任意）
          </label>
          <textarea
            value={form.preferences}
            onChange={(e) => setForm({ ...form, preferences: e.target.value })}
            placeholder="例: グルメ重視、美術館巡り、子連れ、ビーチリゾート..."
            rows={3}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-3 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              プランを生成中...
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              プランを作成する
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-gradient-to-br from-purple-50 to-blue-50 border border-purple-200 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-purple-600" />
            <h2 className="font-semibold text-purple-900">Geminiが作成した旅行プラン</h2>
          </div>
          <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
            {result}
          </div>
        </div>
      )}
    </div>
  );
}
