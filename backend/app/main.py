from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.internal.auth import router as auth_router
from app.api.v1.internal.products import router as products_router
from app.core.config import settings

app = FastAPI(
    title="Credit Tracker API",
    version="0.1.0",
    description="Walking skeleton: Colombia credit card installment (cuota) calculation engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/internal")
app.include_router(products_router, prefix="/api/v1/internal")


@app.get("/health")
async def health():
    return {"status": "ok"}
