"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Heart, Bell, BellOff, Trash2, Star, AlertCircle } from "lucide-react";
import { apiFetch } from "@/lib/api/client";
import { formatPrice } from "@/lib/utils";

interface Favorite {
  id: string;
  origin: string;
  destination: string;
  created_at: string;
}

interface PriceAlert {
  id: string;
  origin: string;
  destination: string;
  threshold_price: number;
  is_active: boolean;
  created_at: string;
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [pushSupported] = useState(
    typeof window !== "undefined" && "serviceWorker" in navigator && "PushManager" in window
  );
  const [pushStatus, setPushStatus] = useState<"idle" | "loading" | "done" | "error">("idle");

  const { data: favorites = [], isLoading: favLoading } = useQuery<Favorite[]>({
    queryKey: ["favorites"],
    queryFn: () => apiFetch("/favorites"),
  });

  const { data: alerts = [], isLoading: alertLoading } = useQuery<PriceAlert[]>({
    queryKey: ["alerts"],
    queryFn: () => apiFetch("/alerts"),
  });

  const deleteFav = useMutation({
    mutationFn: (id: string) => apiFetch(`/favorites/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["favorites"] }),
  });

  const deleteAlert = useMutation({
    mutationFn: (id: string) => apiFetch(`/alerts/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const toggleAlert = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      apiFetch(`/alerts/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const handlePushSubscribe = async () => {
    if (!pushSupported) return;
    setPushStatus("loading");
    try {
      const reg = await navigator.serviceWorker.ready;
      const vapidPublicKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY;
      if (!vapidPublicKey) throw new Error("VAPID key not set");

      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
      });

      await apiFetch("/favorites/push-subscribe", {
        method: "POST",
        body: JSON.stringify({ subscription: sub.toJSON() }),
      });
      setPushStatus("done");
    } catch {
      setPushStatus("error");
    }
  };

  return (
    <div className="max-w-2xl mx-auto pb-24 px-4 pt-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">設定・お気に入り</h1>

      {/* お気に入りルート */}
      <section className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <Heart className="w-5 h-5 text-rose-500" />
          <h2 className="text-lg font-semibold">お気に入りルート</h2>
        </div>
        {favLoading ? (
          <LoadingRows />
        ) : favorites.length === 0 ? (
          <EmptyState message="お気に入りルートがありません" />
        ) : (
          <ul className="space-y-2">
            {favorites.map((fav) => (
              <li
                key={fav.id}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-xl px-4 py-3 shadow-sm"
              >
                <div className="flex items-center gap-2">
                  <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                  <span className="font-medium">
                    {fav.origin} → {fav.destination}
                  </span>
                </div>
                <button
                  onClick={() => deleteFav.mutate(fav.id)}
                  className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
                  aria-label="削除"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* 価格アラート */}
      <section className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <Bell className="w-5 h-5 text-blue-500" />
          <h2 className="text-lg font-semibold">価格アラート</h2>
        </div>
        {alertLoading ? (
          <LoadingRows />
        ) : alerts.length === 0 ? (
          <EmptyState message="価格アラートが設定されていません" />
        ) : (
          <ul className="space-y-2">
            {alerts.map((alert) => (
              <li
                key={alert.id}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-xl px-4 py-3 shadow-sm"
              >
                <div>
                  <div className="font-medium">
                    {alert.origin} → {alert.destination}
                  </div>
                  <div className="text-sm text-gray-500">
                    目標: {formatPrice(alert.threshold_price)}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => toggleAlert.mutate({ id: alert.id, is_active: !alert.is_active })}
                    className={`p-1.5 rounded-lg transition-colors ${
                      alert.is_active
                        ? "text-blue-600 bg-blue-50"
                        : "text-gray-400 bg-gray-100"
                    }`}
                    aria-label={alert.is_active ? "無効化" : "有効化"}
                  >
                    {alert.is_active ? (
                      <Bell className="w-4 h-4" />
                    ) : (
                      <BellOff className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={() => deleteAlert.mutate(alert.id)}
                    className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
                    aria-label="削除"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* プッシュ通知 */}
      <section className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <Bell className="w-5 h-5 text-green-500" />
          <h2 className="text-lg font-semibold">プッシュ通知</h2>
        </div>
        {!pushSupported ? (
          <div className="flex items-center gap-2 text-sm text-gray-500 bg-gray-50 rounded-xl p-4">
            <AlertCircle className="w-4 h-4" />
            このブラウザはWeb Push通知に対応していません
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl px-4 py-4 shadow-sm">
            <p className="text-sm text-gray-600 mb-4">
              セール情報や価格アラートをプッシュ通知で受け取れます。
            </p>
            {pushStatus === "done" ? (
              <div className="flex items-center gap-2 text-green-600 text-sm font-medium">
                <Bell className="w-4 h-4" />
                プッシュ通知が有効です
              </div>
            ) : (
              <button
                onClick={handlePushSubscribe}
                disabled={pushStatus === "loading"}
                className="w-full py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {pushStatus === "loading" ? "登録中..." : "通知を有効にする"}
              </button>
            )}
            {pushStatus === "error" && (
              <p className="text-sm text-red-500 mt-2">
                通知の登録に失敗しました。ブラウザの設定をご確認ください。
              </p>
            )}
          </div>
        )}
      </section>

      {/* アプリ情報 */}
      <section>
        <h2 className="text-lg font-semibold mb-3">アプリ情報</h2>
        <div className="bg-white border border-gray-200 rounded-xl px-4 py-4 shadow-sm space-y-2 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>バージョン</span>
            <span className="font-medium">1.0.0</span>
          </div>
          <div className="flex justify-between">
            <span>データソース</span>
            <span className="font-medium">Amadeus API / JAL・ANA・LCC RSS</span>
          </div>
          <div className="flex justify-between">
            <span>AIプランナー</span>
            <span className="font-medium">Gemini 1.5 Flash</span>
          </div>
        </div>
      </section>
    </div>
  );
}

function LoadingRows() {
  return (
    <div className="space-y-2">
      {[...Array(2)].map((_, i) => (
        <div key={i} className="h-14 bg-gray-100 rounded-xl animate-pulse" />
      ))}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-8 text-gray-400 text-sm bg-gray-50 rounded-xl">{message}</div>
  );
}

function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}
