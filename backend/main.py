from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="TravelApp API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
from routers import flights, sales, airports, favorites, alerts, ai, internal
app.include_router(flights.router)
app.include_router(sales.router)
app.include_router(airports.router)
app.include_router(favorites.router)
app.include_router(alerts.router)
app.include_router(ai.router)
app.include_router(internal.router)


@app.get("/")
def root():
    return {"message": "TravelApp API"}


@app.get("/health")
def health():
    return {"status": "ok"}
