# TravelApp

フライト最安値検索・セールカレンダー・AIプランナー・どこでも検索を備えた個人向け旅行アプリ（PWA）。

## 技術スタック

| 層 | 技術 |
|---|---|
| フロントエンド | Next.js 15 (App Router) + TypeScript + Tailwind CSS |
| バックエンド | FastAPI + Python 3.12 + SQLAlchemy 2 |
| DB | Neon (PostgreSQL / サーバーレス) |
| デプロイ | Cloud Run (backend) + Vercel (frontend) |
| 外部API | Amadeus, Kiwi, Gemini 1.5 Flash |

## ローカル起動手順

### 1. 環境変数の設定

```bash
# バックエンド
cp backend/.env.example backend/.env
# .env を編集して各APIキーを設定

# フロントエンド
cp frontend/.env.local.example frontend/.env.local
# .env.local を編集
```

### 2. バックエンド起動

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python init_db.py           # テーブル作成
python scripts/seed_airports.py  # 空港データ投入
uvicorn main:app --reload --port 8000
```

### 3. フロントエンド起動

```bash
cd frontend
npm install
npm run dev
```

ブラウザで http://localhost:3000 を開く。

### Docker Compose（一括起動）

```bash
cp backend/.env.example .env   # ルートに .env を作成して編集
docker compose up --build
```

## 必要な環境変数（backend/.env）

| 変数名 | 説明 |
|---|---|
| `DATABASE_URL` | Neon の接続文字列（`postgresql+asyncpg://...`） |
| `AMADEUS_CLIENT_ID` | Amadeus API クライアントID |
| `AMADEUS_CLIENT_SECRET` | Amadeus API クライアントシークレット |
| `GEMINI_API_KEY` | Google AI Studio の APIキー |
| `API_KEY` | フロントエンドとの内部認証キー（任意の文字列） |
| `VAPID_PRIVATE_KEY` | Web Push 用 VAPID 秘密鍵 |
| `VAPID_PUBLIC_KEY` | Web Push 用 VAPID 公開鍵 |
| `VAPID_EMAIL` | Web Push 用メールアドレス |

VAPID キーの生成:
```bash
pip install pywebpush
python -c "from py_vapid import Vapid; v = Vapid(); v.generate_keys(); print(v.private_pem().decode()); print(v.public_key)"
```

## デプロイ

詳細は `docs/` 以下のドキュメントを参照。

- Cloud Run: `backend/fly.toml` (Fly.io も選択可)
- Vercel: `frontend/vercel.json` でAPIリバースプロキシ設定済み

## 主な画面

| パス | 説明 |
|---|---|
| `/` | トップ（フライト検索 + 今日のセール） |
| `/calendar` | セールカレンダー |
| `/flights/search` | フライト検索結果 |
| `/flights/price-calendar` | 月次価格カレンダー |
| `/inspire` | どこでも検索（格安行き先発見） |
| `/ai-plan` | AI旅行プランナー（Gemini） |
| `/settings` | お気に入り・価格アラート・通知設定 |
